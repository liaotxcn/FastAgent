from typing import Dict, Any, Optional, List, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.agent.registry import get_agent_descriptions, get_agent_info
from app.agent.base import ToolAgent
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
    
    return True

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
        self._route_cache = {}
    
    def _get_agent(self, agent_type: str):
        if agent_type not in self._agent_cache:
            info = get_agent_info(agent_type)
            agent_class = info.get("class")

            if agent_class == "ToolAgent":
                self._agent_cache[agent_type] = ToolAgent(
                    tools=info["tools"](),
                    system_prompt=info["system_prompt"]
                )
            elif agent_class == "GeneralAgent":
                self._agent_cache[agent_type] = GeneralAgent()
            elif agent_class == "VisionAgent":
                self._agent_cache[agent_type] = VisionAgent()
            else:
                self._agent_cache[agent_type] = GeneralAgent()
        return self._agent_cache[agent_type]
    
    def _keyword_match(self, user_question: str) -> Optional[Dict[str, Any]]:
        """Tier 1: 关键词匹配路由，返回 None 表示需要 LLM 路由"""
        from app.agent.registry import AGENT_REGISTRY
        question_lower = user_question.lower()
        scores = {}
        for agent_type, info in AGENT_REGISTRY.items():
            keywords = info.get("keywords", [])
            score = sum(1 for kw in keywords if kw.lower() in question_lower)
            if score > 0:
                scores[agent_type] = score
        if not scores:
            return None
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_agent, best_score = sorted_agents[0]
        second_score = sorted_agents[1][1] if len(sorted_agents) > 1 else 0
        if (best_score >= 2 and best_score - second_score >= 2) or len(scores) == 1:
            logger.info(f"Keyword match: {best_agent} (score={best_score})")
            return {"agent_type": best_agent, "reason": f"关键词匹配 (score={best_score})", "task": user_question}
        return None

    async def _smart_route(self, user_question: str) -> Dict[str, Any]:
        """分级路由：关键词匹配优先，LLM 兜底，含缓存"""
        cache_key = user_question.strip().lower()
        if cache_key in self._route_cache:
            logger.info(f"Route cache hit: {self._route_cache[cache_key]['agent_type']}")
            return self._route_cache[cache_key]
        result = self._keyword_match(user_question)
        if result is None:
            result = await self._route(user_question)
        if len(self._route_cache) >= 100:
            self._route_cache.pop(next(iter(self._route_cache)))
        self._route_cache[cache_key] = result
        return result
    
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
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                
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
                      session_id: Optional[str] = None, images: Optional[List[str]] = None,
                      user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            # 验证图像是否有效
            valid_images = get_valid_images(images)
            
            # 确保会话关联到用户
            if session_id and user_id:
                session_exists = await redis_service.get_session(session_id)
                if session_exists:
                    list_key = f"chat:sessions:user:{user_id}"
                    await redis_service.redis_client.sadd(list_key, session_id)
                    await redis_service.redis_client.expire(list_key, settings.redis_session_ttl)
                    logger.info(f"Associated session {session_id} to user {user_id}")
            
            # 构建上下文：从Redis获取历史消息
            if session_id:
                history_messages = await redis_service.get_messages(session_id)
                if history_messages:
                    # 构建上下文消息
                    context_messages = []
                    for msg in history_messages:
                        context_messages.append(f"{msg['role']}: {msg['content']}")
                    # 将历史消息添加到上下文
                    if context is None:
                        context = {}
                    context["history"] = "\n".join(context_messages)
            
            if valid_images:
                route_result = {"agent_type": "vision", "reason": f"检测到{len(valid_images)}张图像输入", "task": user_question}
                logger.info(f"{len(valid_images)} images detected, routing to VisionAgent")
            else:
                # 当没有有效图像时，使用通用Agent
                route_result = await self._smart_route(user_question)
                logger.info(f"Routed to {route_result['agent_type']}")
            
            agent = self._get_agent(route_result["agent_type"])
            
            if route_result["agent_type"] == "vision":
                result = await agent.execute(route_result["task"], context, valid_images)
            else:
                result = await agent.execute(route_result["task"], context)
            
            result["data"]["agent_type"] = route_result["agent_type"]
            result["data"]["route_reason"] = route_result.get("reason", "")
            
            if session_id:
                await redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(valid_images), "image_count": len(valid_images) if valid_images else 0},
                    user_id=user_id
                )
                await redis_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=result["data"].get("output", ""),
                    agent_type=route_result["agent_type"],
                    metadata={"route_reason": route_result.get("reason", "")},
                    user_id=user_id
                )
            
            return result
        except Exception as e:
            logger.exception(f"Router failed: {str(e)}")
            if session_id:
                await redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(valid_images), "image_count": len(valid_images) if valid_images else 0},
                    user_id=user_id
                )
            result = await self._get_agent("general").execute(user_question, context)
            result["data"]["agent_type"] = "general"
            result["data"]["route_reason"] = "路由失败，使用通用Agent"
            if session_id:
                await redis_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=result["data"].get("output", ""),
                    agent_type="general",
                    metadata={"route_reason": "路由失败，使用通用Agent"},
                    user_id=user_id
                )
            return result
    
    async def stream_execute(self, user_question: str, context: Optional[Dict[str, Any]] = None,
                            session_id: Optional[str] = None, images: Optional[List[str]] = None,
                            user_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行路由和任务"""
        try:
            valid_images = get_valid_images(images)
            
            # 确保会话关联到用户
            if session_id and user_id:
                session_exists = await redis_service.get_session(session_id)
                if session_exists:
                    list_key = f"chat:sessions:user:{user_id}"
                    await redis_service.redis_client.sadd(list_key, session_id)
                    await redis_service.redis_client.expire(list_key, settings.redis_session_ttl)
                    logger.info(f"Associated session {session_id} to user {user_id}")
            
            # 构建上下文：从Redis获取历史消息
            if session_id:
                history_messages = await redis_service.get_messages(session_id)
                if history_messages:
                    # 构建上下文消息
                    context_messages = []
                    for msg in history_messages:
                        context_messages.append(f"{msg['role']}: {msg['content']}")
                    # 将历史消息添加到上下文
                    if context is None:
                        context = {}
                    context["history"] = "\n".join(context_messages)
            
            if valid_images:
                route_result = {"agent_type": "vision", "reason": f"检测到{len(valid_images)}张图像输入", "task": user_question}
                logger.info(f"{len(valid_images)} images detected, routing to VisionAgent")
            else:
                yield {"type": "status", "content": "正在分析问题..."}
                route_result = await self._smart_route(user_question)
                logger.info(f"Routed to {route_result['agent_type']}")
            
            agent = self._get_agent(route_result["agent_type"])
            
            yield {
                "type": "metadata",
                "agent_type": route_result["agent_type"],
                "route_reason": route_result.get("reason", "")
            }
            
            full_response = ""
            
            if route_result["agent_type"] == "vision":
                async for chunk in agent.stream_execute(route_result["task"], context, valid_images):
                    full_response += chunk
                    yield {"type": "content", "content": chunk}
            else:
                async for chunk in agent.stream_execute(route_result["task"], context):
                    full_response += chunk
                    yield {"type": "content", "content": chunk}
            
            if session_id:
                await redis_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_question,
                    metadata={"has_image": bool(valid_images), "image_count": len(valid_images) if valid_images else 0},
                    user_id=user_id
                )
                await redis_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    agent_type=route_result["agent_type"],
                    metadata={"route_reason": route_result.get("reason", "")},
                    user_id=user_id
                )
        
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Router streaming failed: {error_msg}")
            yield {"type": "error", "content": f"处理失败: {error_msg}"}