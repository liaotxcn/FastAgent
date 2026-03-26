from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic.v1 import BaseModel, Field
import httpx
from app.config import settings

class MCPToolInput(BaseModel):
    tool_name: str = Field(description="Name of the MCP tool to execute")
    parameters: dict = Field(description="Parameters for the MCP tool")

class MCPToolWrapper(BaseTool):
    name = settings.mcp_tool_name
    description = settings.mcp_tool_description
    args_schema: Type[BaseModel] = MCPToolInput
    
    async def _arun(self, tool_name: str, parameters: dict) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.mcp_server_url}/tools/{tool_name}",
                    json=parameters,
                    timeout=settings.mcp_request_timeout
                )
                response.raise_for_status()
                return f"MCP tool '{tool_name}' executed successfully: {response.json()}"
            except Exception as e:
                return f"Error executing MCP tool: {str(e)}"
    
    def _run(self, tool_name: str, parameters: dict) -> str:
        import asyncio
        return asyncio.run(self._arun(tool_name, parameters))
