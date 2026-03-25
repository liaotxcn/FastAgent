from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MCPToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class DatabaseQueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

class AgentExecuteRequest(BaseModel):
    task: str
    agent_type: str
    context: Optional[Dict[str, Any]] = None
