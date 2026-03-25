from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import settings
import re

class BaseAgent(ABC):
    def __init__(self, model_name: str = None, temperature: float = 0.3):
        model = model_name or settings.modelscope_model_id
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=settings.modelscope_api_key,
            openai_api_base=settings.modelscope_api_base
        )
        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()
    
    @abstractmethod
    def _get_tools(self) -> list:
        pass
    
    def _create_agent(self) -> AgentExecutor:
        # REACT 提示模板
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the tool to use, should be one of [{tool_names}]
Action Input: the input to the tool
Observation: the result of the tool
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"]
        )
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            return_only_outputs=False,
            max_iterations=10,
            early_stopping_method="force",
            handle_parsing_errors=True
        )
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 构建工具描述
            tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            tool_names = ", ".join([tool.name for tool in self.tools])
            
            result = await self.agent_executor.ainvoke({
                "input": task,
                "tools": tools_description,
                "tool_names": tool_names
            })
            return {
                "success": True,
                "message": "Task completed successfully",
                "data": result
            }
        except Exception as e:
            error_msg = str(e)
            # 检查是否是输出解析错误，并且包含查询结果
            if "output parsing error" in error_msg.lower() and ("查询结果" in error_msg or "用户" in error_msg or "ID" in error_msg):
                # 提取查询结果
                import re
                match = re.search(r'Could not parse LLM output: `(.+?)`,', error_msg, re.DOTALL)
                if match:
                    query_result = match.group(1)
                    return {
                        "success": True,
                        "message": "Task completed successfully",
                        "data": {
                            "input": task,
                            "output": query_result
                        }
                    }
            return {
                "success": False,
                "message": "Task failed",
                "error": str(e)
            }
