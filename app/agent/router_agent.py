from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import settings
from app.agent.registry import get_agent_descriptions
from app.agent.db_agent import DatabaseAgent
from app.agent.mcp_agent import MCPAgent
from app.agent.general_agent import GeneralAgent
from loguru import logger
import json

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
        response = await self.llm.ainvoke(f"{formatted_prompt}\n\n问题：{user_question}")
        
        try:
            result = json.loads(response.content.strip())
            result.setdefault("agent_type", "general")
            result.setdefault("task", user_question)
            return result
        except json.JSONDecodeError:
            return {"agent_type": "general", "reason": "解析失败", "task": user_question}
    
    async def execute(self, user_question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            route_result = await self._route(user_question)
            logger.info(f"Routed to {route_result['agent_type']}")
            
            agent = self._get_agent(route_result["agent_type"])
            result = await agent.execute(route_result["task"], context)
            
            result["data"]["agent_type"] = route_result["agent_type"]
            result["data"]["route_reason"] = route_result.get("reason", "")
            
            return result
        except Exception as e:
            logger.exception(f"Router failed: {str(e)}")
            return await self._get_agent("general").execute(user_question, context)