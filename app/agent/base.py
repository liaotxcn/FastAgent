from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, List, Tuple
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from app.config import settings
from app.database.connection import AsyncSessionLocal
from app.database.models import AgentCallHistory
from loguru import logger
import re
import json
from langchain_core.messages import BaseMessage
import time
from datetime import datetime
import tiktoken


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


class HarnessContextManager:
    """上下文边界管理器"""
    def __init__(self):
        self.context_rules = {}
        self.max_context_tokens = 4096
        self._tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def build_context(self, task: str, history: Optional[List[Dict]] = None, constraints: Optional[Dict] = None) -> Dict:
        """构建结构化上下文"""
        context = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "constraints": constraints or {},
            "history": history or []
        }
        self._trim_context(context)
        return context
    
    def _count_tokens(self, text: str) -> int:
        """计算文本的 token 数量"""
        return len(self._tokenizer.encode(str(text)))
    
    def _trim_context(self, context: Dict):
        """基于 token 数量裁剪上下文"""
        if not isinstance(context, dict) or not context.get("history"):
            return
        
        total_tokens = self._count_tokens(str(context["task"])) + self._count_tokens(str(context["constraints"]))
        history = context["history"]
        trimmed_history = []
        
        for msg in reversed(history):
            msg_tokens = self._count_tokens(str(msg))
            if total_tokens + msg_tokens <= self.max_context_tokens:
                trimmed_history.insert(0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        context["history"] = trimmed_history


class HarnessToolManager:
    """工具系统管理器"""
    def __init__(self, tools: List):
        self.tools = tools
        self.tool_capabilities = self._analyze_tool_capabilities()
    
    def _analyze_tool_capabilities(self) -> Dict:
        """分析工具能力"""
        capabilities = {}
        for tool in self.tools:
            capabilities[tool.name] = {
                "description": tool.description,
                "args": getattr(tool, "args", {})
            }
        return capabilities
    
    def select_tools(self, task: str) -> List:
        """根据任务选择合适的工具"""
        selected_tools = []
        for tool in self.tools:
            if self._is_tool_relevant(tool, task):
                selected_tools.append(tool)
        return selected_tools
    
    def _is_tool_relevant(self, tool, task: str) -> bool:
        """判断工具是否与任务相关"""
        return tool.description.lower() in task.lower() or any(keyword in task.lower() for keyword in self._extract_keywords(tool.description))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        return [word.lower() for word in text.split() if len(word) > 3]


class HarnessMemoryManager:
    """记忆与状态管理器"""
    def __init__(self):
        self.short_term_memory = {}
        self.long_term_memory = {}
    
    def store_short_term(self, key: str, value: Any, ttl: int = 3600):
        """存储短期记忆"""
        self.short_term_memory[key] = {
            "value": value,
            "expiry": time.time() + ttl
        }
    
    def store_long_term(self, key: str, value: Any):
        """存储长期记忆"""
        self.long_term_memory[key] = value
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        # 先检查短期记忆
        if key in self.short_term_memory:
            memory = self.short_term_memory[key]
            if time.time() < memory["expiry"]:
                return memory["value"]
            else:
                del self.short_term_memory[key]
        
        # 再检查长期记忆
        return self.long_term_memory.get(key)


class HarnessEvaluationManager:
    """评估与观测管理器"""
    def __init__(self):
        self.metrics = {}
    
    def evaluate_result(self, task: str, result: Dict) -> Dict:
        """评估执行结果"""
        evaluation = {
            "task_relevance": self._evaluate_relevance(task, result),
            "completeness": self._evaluate_completeness(result),
            "timeliness": self._evaluate_timeliness(result)
        }
        
        # 计算综合评分
        evaluation["overall_score"] = sum(evaluation.values()) / len(evaluation)
        
        return evaluation
    
    def _evaluate_relevance(self, task: str, result: Dict) -> float:
        """评估结果与任务的相关性"""
        output = result.get("output", "")
        task_keywords = set(self._extract_keywords(task))
        output_keywords = set(self._extract_keywords(output))
        
        if not task_keywords:
            return 1.0
        
        intersection = task_keywords.intersection(output_keywords)
        return len(intersection) / len(task_keywords)
    
    def _evaluate_completeness(self, result: Dict) -> float:
        """评估结果的完整性"""
        output = result.get("output", "")
        return min(1.0, len(output) / 500)  
    
    def _evaluate_timeliness(self, result: Dict) -> float:
        """评估执行的及时性"""
        duration = result.get("execution_state", {}).get("duration", 0)
        return max(0.0, 1.0 - (duration / 30))  # 30秒内为满分
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        return [word.lower() for word in text.split() if len(word) > 3]


class HarnessConstraintManager:
    """约束校验与恢复管理器"""
    def __init__(self):
        self.constraints = {
            "safety": "避免生成有害、歧视性或违法内容",
            "privacy": "保护用户隐私，不泄露个人信息",
            "accuracy": "确保提供准确的信息，不传播错误内容",
            "relevance": "确保回答与用户问题相关，不偏离主题"
        }
    
    def validate_input(self, task: str) -> Tuple[bool, Optional[str]]:
        """验证输入是否符合约束"""
        if any(prohibited in task.lower() for prohibited in ["违法", "诈骗", "隐私", "攻击"]):
            return False, "输入包含违反约束的内容"
        return True, None
    
    def validate_output(self, output: str) -> Tuple[bool, Optional[str]]:
        """验证输出是否符合约束"""
        if any(prohibited in output.lower() for prohibited in ["违法", "歧视", "隐私"]):
            return False, "输出包含违反约束的内容"
        return True, None
    
    def recover_from_error(self, error: Exception) -> Dict:
        """从错误中恢复"""
        error_type = type(error).__name__
        recovery_strategies = {
            "TimeoutError": {"action": "重试", "max_attempts": 3},
            "ConnectionError": {"action": "重试", "max_attempts": 2},
            "ValueError": {"action": "回滚", "message": "输入参数错误"}
        }
        
        return recovery_strategies.get(error_type, {"action": "跳过", "message": "未知错误"})

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
        
        # 初始化 Harness 管理器
        self.context_manager = HarnessContextManager()
        self.tool_manager = HarnessToolManager(self.tools)
        self.memory_manager = HarnessMemoryManager()
        self.evaluation_manager = HarnessEvaluationManager()
        self.constraint_manager = HarnessConstraintManager()
        
        # 存储执行历史
        self.execution_history = []
    
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
    
    @staticmethod
    def _parse_history(history):
        """将历史消息解析为统一的消息列表格式"""
        messages = []
        if not history:
            return messages
        if isinstance(history, str):
            for line in history.split('\n'):
                if line:
                    if ': ' in line:
                        role, content = line.split(': ', 1)
                        messages.append({"role": role, "content": content})
                    else:
                        messages.append({"role": "user", "content": line})
        elif isinstance(history, list):
            for msg in history:
                if isinstance(msg, dict):
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
                else:
                    messages.append({"role": "user", "content": str(msg)})
        return messages
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        pass
    
    async def stream_execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """流式执行任务"""
        history_id = None
        execution_state = None
        full_response = ""
        
        try:
            # 1. 输入验证
            valid, error_msg = self.constraint_manager.validate_input(task)
            if not valid:
                yield f"处理失败: {error_msg}"
                return
            
            # 2. 构建结构化上下文
            if context and isinstance(context, str):
                try:
                    context = json.loads(context)
                except json.JSONDecodeError:
                    context = None
            
            structured_context = self.context_manager.build_context(
                task=task,
                history=context.get("history") if isinstance(context, dict) else None,
                constraints=self.constraint_manager.constraints
            )
            
            # 3. 选择合适的工具
            selected_tools = self.tool_manager.select_tools(task)
            
            # 记录调用开始
            async with AsyncSessionLocal() as session:
                history = AgentCallHistory(
                    agent_type=self.__class__.__name__,
                    task=task,
                    context=json.dumps(structured_context),
                    success=1
                )
                session.add(history)
                await session.commit()
                await session.refresh(history)
                history_id = history.id
            
            # 4. 执行任务
            execution_state = {"start_time": time.time()}
            
            # 若有工具 --> 使用 agent 流式执行
            if self.tools:
                messages = self._parse_history(structured_context.get("history"))
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
                system_prompt = self._get_system_prompt()
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(self._parse_history(structured_context.get("history")))
                messages.append({"role": "user", "content": task})
                
                async for chunk in self.llm.astream(messages):
                    if chunk.content:
                        full_response += chunk.content
                        yield chunk.content
            
            # 5. 输出验证
            valid, error_msg = self.constraint_manager.validate_output(full_response)
            if not valid:
                yield f"处理失败: {error_msg}"
                return
            
            # 6. 评估执行结果
            execution_state["duration"] = time.time() - execution_state["start_time"]
            data = {"input": task, "output": full_response, "execution_state": execution_state}
            evaluation = self.evaluation_manager.evaluate_result(task, data)
            data["evaluation"] = evaluation
            
            # 7. 存储执行历史和记忆
            self.execution_history.append({
                "task": task,
                "result": data,
                "evaluation": evaluation,
                "timestamp": datetime.now().isoformat()
            })
            
            # 存储到短期记忆
            self.memory_manager.store_short_term(
                key=f"task_{int(time.time())}",
                value={"task": task, "output": full_response}
            )
            
            # 记录调用成功
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        history.result = json.dumps(data)
                        history.evaluation = json.dumps(evaluation)
                        await session.commit()
            
            logger.info(f"Agent streaming completed: {self.__class__.__name__}")
        
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Agent streaming failed: {error_msg}")
            
            # 8. 错误处理和恢复
            recovery_strategy = self.constraint_manager.recover_from_error(e)
            
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        history.success = 0
                        history.error_message = error_msg
                        history.recovery_strategy = json.dumps(recovery_strategy)
                        await session.commit()
            
            # 检查是否是输出解析错误，并且包含查询结果
            if "output parsing error" in error_msg.lower() and ("查询结果" in error_msg or "用户" in error_msg or "ID" in error_msg):
                # 提取查询结果
                match = re.search(r'Could not parse LLM output: `(.+?)`', error_msg, re.DOTALL)
                if match:
                    query_result = match.group(1)
                    yield query_result
                    
                    # 更新历史记录
                    if history_id:
                        async with AsyncSessionLocal() as session:
                            history = await session.get(AgentCallHistory, history_id)
                            if history:
                                # 构建结果数据
                                data = {
                                    "input": task,
                                    "output": query_result,
                                    "execution_state": execution_state
                                }
                                # 评估执行结果
                                evaluation = self.evaluation_manager.evaluate_result(task, data)
                                data["evaluation"] = evaluation
                                
                                history.success = 1
                                history.result = json.dumps(data)
                                history.evaluation = json.dumps(evaluation)
                                history.error_message = None
                                history.tool_name = "database_query"
                                # 尝试从任务中提取查询语句
                                query_match = re.search(r'SELECT.*', task, re.IGNORECASE | re.DOTALL)
                                if query_match:
                                    history.tool_input = json.dumps({"query": query_match.group(0)})
                                await session.commit()
                    return
            
            yield f"处理失败: {error_msg}"
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        history_id = None
        execution_state = None
        
        try:
            # 1. 输入验证
            valid, error_msg = self.constraint_manager.validate_input(task)
            if not valid:
                return {
                    "success": False,
                    "message": "Input validation failed",
                    "data": {
                        "input": task,
                        "output": ""
                    },
                    "error": error_msg
                }
            
            # 2. 构建结构化上下文
            # 处理 context 参数，确保它是一个字典
            if context and isinstance(context, str):
                try:
                    context = json.loads(context)
                except json.JSONDecodeError:
                    context = None
            
            structured_context = self.context_manager.build_context(
                task=task,
                history=context.get("history") if isinstance(context, dict) else None,
                constraints=self.constraint_manager.constraints
            )
            
            # 3. 选择合适的工具
            selected_tools = self.tool_manager.select_tools(task)
            
            # 记录调用开始
            logger.info(f"Starting agent execution: {self.__class__.__name__}, task: {task}")
            async with AsyncSessionLocal() as session:
                history = AgentCallHistory(
                    agent_type=self.__class__.__name__,
                    task=task,
                    context=json.dumps(structured_context),
                    success=1
                )
                session.add(history)
                await session.commit()
                await session.refresh(history)
                history_id = history.id
            
            # 4. 执行任务
            execution_state = {"start_time": time.time()}
            
            messages = self._parse_history(structured_context.get("history"))
            messages.append({"role": "user", "content": task})
            
            result = await self.agent.ainvoke({
                "messages": messages
            })
            
            # 5. 序列化结果
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
            
            # 6. 输出验证
            valid, error_msg = self.constraint_manager.validate_output(data.get("output", ""))
            if not valid:
                return {
                    "success": False,
                    "message": "Output validation failed",
                    "data": data,
                    "error": error_msg
                }
            
            # 7. 评估执行结果
            evaluation = self.evaluation_manager.evaluate_result(task, data)
            data["evaluation"] = evaluation
            execution_state["duration"] = time.time() - execution_state["start_time"]
            data["execution_state"] = execution_state
            
            # 8. 存储执行历史和记忆
            self.execution_history.append({
                "task": task,
                "result": data,
                "evaluation": evaluation,
                "timestamp": datetime.now().isoformat()
            })
            
            # 存储到短期记忆
            self.memory_manager.store_short_term(
                key=f"task_{int(time.time())}",
                value={"task": task, "output": data.get("output", "")}
            )
            
            # 9. 记录调用成功
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
                    history.result = json.dumps(data)
                    history.evaluation = json.dumps(evaluation)
                    await session.commit()
            
            return {
                "success": True,
                "message": "Task completed successfully",
                "data": data,
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Agent execution failed: {error_msg}")
            
            # 10. 错误处理和恢复
            recovery_strategy = self.constraint_manager.recover_from_error(e)
            
            # 记录调用失败
            if history_id:
                async with AsyncSessionLocal() as session:
                    history = await session.get(AgentCallHistory, history_id)
                    if history:
                        history.success = 0
                        history.error_message = error_msg
                        history.recovery_strategy = json.dumps(recovery_strategy)
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
                                # 构建结果数据
                                data = {
                                    "input": task,
                                    "output": query_result,
                                    "execution_state": execution_state
                                }
                                # 评估执行结果
                                evaluation = self.evaluation_manager.evaluate_result(task, data)
                                data["evaluation"] = evaluation
                                
                                history.result = json.dumps(data)
                                history.evaluation = json.dumps(evaluation)
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
                            "output": query_result,
                            "execution_state": execution_state
                        },
                        "error": None
                    }
            return {
                "success": False,
                "message": "Task failed",
                "data": {
                    "input": task,
                    "output": "",
                    "execution_state": execution_state,
                    "recovery_strategy": recovery_strategy
                },
                "error": str(e)
            }


class ToolAgent(BaseAgent):
    """通用工具型 Agent，通过配置即可创建，无需新建子类文件"""

    def __init__(self, tools: list, system_prompt: str, model_name=None, temperature=None):
        self._tools = tools
        self._system_prompt = system_prompt
        super().__init__(model_name, temperature)

    def _get_tools(self) -> list:
        return self._tools

    def _get_system_prompt(self) -> str:
        return self._system_prompt
