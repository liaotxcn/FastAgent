from typing import List
from app.agent.base import BaseAgent

class GeneralAgent(BaseAgent):
    def _get_tools(self) -> List:
        return []
    
    def _get_system_prompt(self) -> str:
        return """你是一个友好的AI助手，可以帮助用户回答一般性问题。
        
        回答要求：简洁明了、友好自然。如果问题涉及数据库或工具调用，告诉用户你可以帮助处理。"""