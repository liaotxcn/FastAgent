from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.database.models import AgentCallHistory
from loguru import logger
import re
import json
from langchain_core.messages import BaseMessage


def serialize_message(message):
    """将LangChain消息对象转换为可序列化的字典"""
    if isinstance(message, BaseMessage):
        return {
            "role": message.type,
            "content": message.content
        }
    return message


def serialize_result(result):
    """递归处理结果中的消息对象"""
    if isinstance(result, dict):
        return {k: serialize_result(v) for k, v in result.items()}
    elif isinstance(result, list):
        return [serialize_result(item) for item in result]
    elif isinstance(result, BaseMessage):
        return serialize_message(result)
    return result

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
        self.agent = self._create_agent()
    
    @abstractmethod
    def _get_tools(self) -> list:
        pass
    
    def _create_agent(self):
        system_prompt = self._get_system_prompt()
        
        # 创建agent
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt
        )
        
        return agent
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass
    
    async def stream_execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """流式执行任务"""
        history_id = None
        try:
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
            
            full_response = ""
            
            # 若有工具 --> 使用 agent 流式执行
            if self.tools:
                # 构建消息列表，包含历史消息
                messages = []
                if context and context.get("history"):
                    # 历史消息格式
                    messages.append({"role": "user", "content": context["history"]})
                messages.append({"role": "user", "content": task})
                
                async for event in self.agent.astream_events(
                    {"messages": messages},
                    version="v1"
                ):
                    if event.get("event") == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content"):
                            content = chunk.content
                            if content:
                                full_response += content
                                yield content
            else:
                # 若无工具 --> 使用 LLM
                system_prompt = self._get_system_prompt()
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # 添加历史消息
                if context and context.get("history"):
                    messages.append({"role": "user", "content": context["history"]})
                
                # 添加当前任务
                messages.append({"role": "user", "content": task})
                
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        full_response += chunk.content
                        yield chunk.content
            
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        serialized_result = serialize_result({"input": task, "output": full_response})
                        history.result = json.dumps(serialized_result)
                        await session.commit()
            
            logger.info(f"Agent streaming completed: {self.__class__.__name__}")
        
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Agent streaming failed: {error_msg}")
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        history.success = 0
                        history.error_message = error_msg
                        await session.commit()
            yield f"处理失败: {error_msg}"
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        history_id = None
        try:
            # 构建工具描述
            tools = self.tools or []
            tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
            tool_names = ", ".join([tool.name for tool in tools])
            
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
            
            # 构建消息列表，包含历史消息
            messages = []
            if context and context.get("history"):
                # 历史消息格式
                messages.append({"role": "user", "content": context["history"]})
            messages.append({"role": "user", "content": task})
            
            result = await self.agent.ainvoke({
                "messages": messages
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
                    # 序列化结果以处理消息对象
                    serialized_result = serialize_result(result)
                    history.result = json.dumps(serialized_result)
                    await session.commit()
            
            # 序列化结果以处理消息对象
            data = serialize_result(result) or {}
            if "input" not in data:
                data["input"] = task
            
            # 从返回格式中提取output
            if "output" not in data:
                # 检查是否有message格式的输出
                if isinstance(data, dict) and "messages" in data:
                    messages = data["messages"]
                    if messages and isinstance(messages, list):
                        for msg in reversed(messages):
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                data["output"] = msg.get("content", "")
                                break
                
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
                                # 序列化结果以处理消息对象
                                serialized_result = serialize_result({"input": task, "output": query_result})
                                history.result = json.dumps(serialized_result)
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
