from typing import Dict, Any, Optional
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
            template="""分析用户问题，选择合适的Agent处理。

可用Agent：
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
                result = json.loads(response_text)
                result.setdefault("agent_type", "general")
                result.setdefault("task", user_question)
                logger.info(f"Route result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse router response: {e}")
                return {"agent_type": "general", "reason": "解析失败", "task": user_question}
        except Exception as e:
            logger.exception(f"Routing failed: {e}")
            return {"agent_type": "general", "reason": "路由失败", "task": user_question}
    
    async def execute(self, user_question: str, context: Optional[Dict[str, Any]] = None, 
                      session_id: Optional[str] = None, image: Optional[str] = None) -> Dict[str, Any]:
        try:
            # 验证图像是否有效
            if image and is_valid_image(image):
                route_result = {"agent_type": "vision", "reason": "检测到图像输入", "task": user_question}
                logger.info(f"Image detected, routing to VisionAgent")
            else:
                # 无有效图像时，使用通用Agent
                route_result = await self._route(user_question)
                logger.info(f"Routed to {route_result['agent_type']}")
            
            agent = self._get_agent(route_result["agent_type"])
            
            if route_result["agent_type"] == "vision":
                result = await agent.execute(route_result["task"], context, image)
            else:
                result = await agent.execute(route_result["task"], context)
            
            result["data"]["agent_type"] = route_result["agent_type"]
            result["data"]["route_reason"] = route_result.get("reason", "")
            
            if session_id:
                redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(image)}
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
                    metadata={"has_image": bool(image)}
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