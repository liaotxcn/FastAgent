from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentRequest(BaseModel):
    task: str
    agent_type: str = "mcp"
    context: Optional[Dict[str, Any]] = None

class MCPToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class DatabaseQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None
