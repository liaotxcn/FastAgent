from typing import List
from app.agent.base import BaseAgent
from app.tools.mcp_tools import MCPToolWrapper

class MCPAgent(BaseAgent):
    def _get_tools(self) -> List:
        return [MCPToolWrapper()]
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful agent that can interact with MCP tools to perform various tasks.
        You have access to MCP (Model Context Protocol) tools that can help you accomplish user requests.
        Use these tools when appropriate to complete the user's task."""
