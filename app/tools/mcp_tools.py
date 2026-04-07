from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import httpx
from loguru import logger
from app.config import settings

class MCPToolInput(BaseModel):
    tool_name: str = Field(description="Name of the MCP tool to execute")
    parameters: dict = Field(description="Parameters for the MCP tool")

class MCPToolWrapper(BaseTool):
    name: str = settings.mcp_tool_name
    description: str = settings.mcp_tool_description
    args_schema: Type[BaseModel] = MCPToolInput
    
    async def _arun(self, tool_name: str, parameters: dict) -> str:
        """执行 MCP 工具"""
        logger.info(f"Executing MCP tool: {tool_name}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.mcp_server_url}/tools/{tool_name}",
                    json=parameters,
                    timeout=settings.mcp_request_timeout
                )
                response.raise_for_status()
                logger.info(f"MCP tool '{tool_name}' executed successfully")
                return f"MCP tool '{tool_name}' executed successfully: {response.json()}"
            except httpx.HTTPStatusError as e:
                logger.error(f"MCP tool error (status {e.response.status_code}): {e.response.text}")
                return f"MCP tool error (status {e.response.status_code}): {e.response.text}"
            except httpx.ConnectError as e:
                logger.error(f"Failed to connect to MCP server: {str(e)}")
                return f"Failed to connect to MCP server: {str(e)}"
            except httpx.TimeoutException as e:
                logger.error(f"MCP tool timeout: {str(e)}")
                return f"MCP tool timeout: {str(e)}"
            except Exception as e:
                logger.exception(f"Error executing MCP tool: {str(e)}")
                return f"Error executing MCP tool: {str(e)}"
    
    def _run(self, tool_name: str, parameters: dict) -> str:
        logger.info(f"Synchronously executing MCP tool: {tool_name}")
        import asyncio
        return asyncio.run(self._arun(tool_name, parameters))
