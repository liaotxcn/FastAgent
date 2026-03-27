from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.database.models import AgentCallHistory
from loguru import logger
import re
import json

class BaseAgent(ABC):
    def __init__(self, model_name: str = None, temperature: float = None):
        model = model_name or settings.modelscope_model_id
        temp = temperature if temperature is not None else settings.agent_temperature
        self.llm = ChatOpenAI(
            model=model,
            temperature=temp,
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
            max_iterations=settings.agent_max_iterations,
            early_stopping_method="force",
            handle_parsing_errors=True
        )
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        history_id = None
        try:
            # 构建工具描述
            tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            tool_names = ", ".join([tool.name for tool in self.tools])
            
            # 记录调用开始
            logger.info(f"Starting agent execution: {self.__class__.__name__}, task: {task}")
            async with AsyncSessionLocal() as session:
                history = AgentCallHistory(
                    agent_type=self.__class__.__name__,
                    task=task,
                    context=json.dumps(context) if context else None,
                    success=1
                )
                session.add(history)
                await session.commit()
                await session.refresh(history)
                history_id = history.id
            
            result = await self.agent_executor.ainvoke({
                "input": task,
                "tools": tools_description,
                "tool_names": tool_names
            })
            
            # 记录调用成功
            async with AsyncSessionLocal() as session:
                history = await session.get(AgentCallHistory, history_id)
                if history:
                    # 初始化工具调用信息
                    tool_name = None
                    tool_input = None
                    tool_output = None
                    
                    # 从 result 中提取工具调用信息
                    if isinstance(result, dict):
                        # 检查是否有工具调用相关的信息
                        if "intermediate_steps" in result:
                            steps = result["intermediate_steps"]
                            if steps and hasattr(steps, '__iter__'):
                                # 取最后一个步骤
                                last_step = steps[-1]
                                
                                # 尝试从 last_step 中提取工具调用信息
                                if isinstance(last_step, tuple) and len(last_step) == 2:
                                    # 元组格式: (tool_call, observation)
                                    tool_call, observation = last_step
                                    if hasattr(tool_call, "name"):
                                        tool_name = tool_call.name
                                    if hasattr(tool_call, "args"):
                                        tool_input = json.dumps(tool_call.args)
                                    tool_output = observation
                                elif isinstance(last_step, dict):
                                    # 字典格式
                                    if "tool_call" in last_step:
                                        tool_call = last_step["tool_call"]
                                        if isinstance(tool_call, dict) and "name" in tool_call:
                                            tool_name = tool_call["name"]
                                            if "args" in tool_call:
                                                tool_input = json.dumps(tool_call["args"])
                                    if "observation" in last_step:
                                        tool_output = last_step["observation"]
                        
                        # 特殊处理：如果是数据库查询，直接设置工具信息
                        if not tool_name and "database" in self.__class__.__name__.lower():
                            tool_name = "database_query"
                            # 尝试从任务中提取查询语句
                            if task:
                                if "SELECT" in task.upper():
                                    tool_input = json.dumps({"query": task})
                            # 尝试从 result 中提取查询结果
                            if "output" in result:
                                tool_output = result["output"]
                    
                    # 记录工具调用信息
                    history.tool_name = tool_name or "unknown"
                    history.tool_input = tool_input or "{}"
                    history.tool_output = tool_output or ""
                    history.result = json.dumps(result)
                    await session.commit()
            
            # 确保 data 对象包含 input 和 output 属性
            data = result or {}
            if "input" not in data:
                data["input"] = task
            if "output" not in data:
                data["output"] = data.get("result", "")
            
            return {
                "success": True,
                "message": "Task completed successfully",
                "data": data,
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Agent execution failed: {error_msg}")
            # 记录调用失败
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        history.success = 0
                        history.error_message = error_msg
                        await session.commit()
            
            # 检查是否是输出解析错误，并且包含查询结果
            if "output parsing error" in error_msg.lower() and ("查询结果" in error_msg or "用户" in error_msg or "ID" in error_msg):
                # 提取查询结果
                match = re.search(r'Could not parse LLM output: `(.+?)`', error_msg, re.DOTALL)
                if match:
                    query_result = match.group(1)
                    # 更新历史记录
                    if history_id:
                        async with AsyncSessionLocal() as session:
                            history = await session.get(AgentCallHistory, history_id)
                            if history:
                                history.success = 1
                                history.result = json.dumps({"input": task, "output": query_result})
                                history.error_message = None
                                history.tool_name = "database_query"
                                # 尝试从任务中提取查询语句
                                query_match = re.search(r'SELECT.*', task, re.IGNORECASE | re.DOTALL)
                                if query_match:
                                    history.tool_input = json.dumps({"query": query_match.group(0)})
                                await session.commit()
                    return {
                        "success": True,
                        "message": "Task completed successfully",
                        "data": {
                            "input": task,
                            "output": query_result
                        },
                        "error": None
                    }
            return {
                "success": False,
                "message": "Task failed",
                "data": {
                    "input": task,
                    "output": ""
                },
                "error": str(e)
            }
