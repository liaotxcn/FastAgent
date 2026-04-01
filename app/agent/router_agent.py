from typing import Dict, Any, Optional, List, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import settings
from app.agent.registry import get_agent_descriptions
from app.agent.db_agent import DatabaseAgent
from app.agent.mcp_agent import MCPAgent
from app.agent.general_agent import GeneralAgent
from app.agent.vision_agent import VisionAgent
from app.services.redis_service import redis_service
from loguru import logger
import json
import re

def is_valid_image(image: Optional[str]) -> bool:
    """验证是否为有效图片"""
    if not image or not isinstance(image, str):
        return False
    
    image = image.strip()
    if not image:
        return False
    
    # 检查是否为 Base64 编码图片
    if image.startswith('data:image/'):
        return True
    
    # 检查是否为有效的图片 URL
    url_pattern = r'^https?://.*\.(jpg|jpeg|png|gif|webp|bmp|svg)'
    if re.match(url_pattern, image, re.IGNORECASE):
        return True
    
    # 检查是否是占位符字符串
    placeholder_patterns = ['string', 'null', 'undefined', 'none', '']
    if image.lower() in placeholder_patterns:
        return False
    
    return False

def has_valid_images(images: Optional[List[str]]) -> bool:
    """检查是否有有效图片"""
    if not images or not isinstance(images, list):
        return False
    
    for image in images:
        if is_valid_image(image):
            return True
    
    return False

def get_valid_images(images: Optional[List[str]]) -> List[str]:
    """获取所有有效图片"""
    if not images or not isinstance(images, list):
        return []
    
    valid_images = []
    for image in images:
        if is_valid_image(image):
            valid_images.append(image)
    
    return valid_images

class RouterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.modelscope_model_id,
            temperature=0.1,
            openai_api_key=settings.modelscope_api_key,
            openai_api_base=settings.modelscope_api_base
        )
        self._agent_cache = {}
    
    def _get_agent(self, agent_type: str):
        if agent_type not in self._agent_cache:
            if agent_type == "database":
                self._agent_cache[agent_type] = DatabaseAgent()
            elif agent_type == "mcp":
                self._agent_cache[agent_type] = MCPAgent()
            elif agent_type == "vision":
                self._agent_cache[agent_type] = VisionAgent()
            else:
                self._agent_cache[agent_type] = GeneralAgent()
        return self._agent_cache[agent_type]
    
    async def _route(self, user_question: str) -> Dict[str, Any]:
        prompt = PromptTemplate(
            template="""你是 FastAgent 的智能路由器，负责分析用户问题并选择最合适的 Agent 处理。

=== 分析要求 ===
1. 仔细理解用户的问题意图
2. 识别问题的核心关键词
3. 匹配最适合的 Agent 类型

=== 可用Agent ===
{agent_descriptions}

返回JSON格式：
{{"agent_type": "类型", "reason": "理由", "task": "任务描述"}}

只返回JSON。""",
            input_variables=["agent_descriptions"]
        )
        
        formatted_prompt = prompt.format(agent_descriptions=get_agent_descriptions())
        logger.info(f"Routing user question: {user_question[:50]}...")
        
        try:
            response = await self.llm.ainvoke(f"{formatted_prompt}\n\n问题：{user_question}")
            response_text = response.content.strip()
            logger.info(f"Router response: {response_text}")
            
            try:
                # 提取JSON内容
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                
                # 清理带引号的键名
                result = {k.strip('"'): v for k, v in result.items()}
                
                return {
                    "agent_type": result.get("agent_type", "general"),
                    "reason": result.get("reason", ""),
                    "task": result.get("task", user_question)
                }
            except Exception as e:
                logger.error(f"Failed to parse router response: {e}")
                return {"agent_type": "general", "reason": "解析失败", "task": user_question}
        except Exception as e:
            logger.exception(f"Routing failed: {e}")
            return {"agent_type": "general", "reason": "路由失败", "task": user_question}
    
    async def execute(self, user_question: str, context: Optional[Dict[str, Any]] = None, 
                      session_id: Optional[str] = None, images: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            # 验证图像是否有效
            valid_images = get_valid_images(images)
            if valid_images:
                route_result = {"agent_type": "vision", "reason": f"检测到{len(valid_images)}张图像输入", "task": user_question}
                logger.info(f"{len(valid_images)} images detected, routing to VisionAgent")
            else:
                # 当没有有效图像时，使用通用Agent
                route_result = await self._route(user_question)
                logger.info(f"Routed to {route_result['agent_type']}")
            
            agent = self._get_agent(route_result["agent_type"])
            
            if route_result["agent_type"] == "vision":
                result = await agent.execute(route_result["task"], context, valid_images)
            else:
                result = await agent.execute(route_result["task"], context)
            
            result["data"]["agent_type"] = route_result["agent_type"]
            result["data"]["route_reason"] = route_result.get("reason", "")
            
            if session_id:
                redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(valid_images), "image_count": len(valid_images) if valid_images else 0}
                )
                redis_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=result["data"].get("output", ""),
                    agent_type=route_result["agent_type"],
                    metadata={"route_reason": route_result.get("reason", "")}
                )
            
            return result
        except Exception as e:
            logger.exception(f"Router failed: {str(e)}")
            if session_id:
                redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(valid_images), "image_count": len(valid_images) if valid_images else 0}
                )
            result = await self._get_agent("general").execute(user_question, context)
            result["data"]["agent_type"] = "general"
            result["data"]["route_reason"] = "路由失败，使用通用Agent"
            if session_id:
                redis_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=result["data"].get("output", ""),
                    agent_type="general",
                    metadata={"route_reason": "路由失败，使用通用Agent"}
                )
            return result