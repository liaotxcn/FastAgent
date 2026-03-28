from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MCPToolRequest(BaseModel):
    tool_name: str = Field(
        ..., 
        description="Name of the MCP tool to execute",
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$'

    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parameters for the tool"
    )
    
    @validator('parameters')
    def validate_parameters(cls, v):
        # 限制参数数量
        if len(v) > 10:
            raise ValueError("Too many parameters, maximum is 10")
        
        # 限制参数值大小
        for key, value in v.items():
            if len(str(value)) > 1000:
                raise ValueError(f"Parameter '{key}' value too large, maximum length is 1000 characters")
        return v

class DatabaseQueryRequest(BaseModel):
    query: str = Field(
        ..., 
        description="SQL query to execute",
        min_length=5,
        max_length=1000
    )
    params: Optional[Dict[str, Any]] = None
    limit: int = Field(
        default=100, 
        ge=1, 
        le=1000, 
        description="Maximum number of rows to return"
    )
    
    @validator('query')
    def validate_sql_query(cls, v):
        # 白名单机制：只允许 SELECT 查询
        if not re.match(r'^\s*SELECT\s', v, re.IGNORECASE):
            raise ValueError("Only SELECT queries are allowed")
        
        # 检测潜在的 SQL 注入攻击
        dangerous_patterns = [
            r'\b(DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE|CREATE|RENAME|REPLACE|GRANT|REVOKE)\b',
            r'\b(EXEC|EXECUTE|xp_)\b',
            r'\bUNION\b.*\bSELECT\b',
            r'--',
            r'\bOR\b.*\b1=1\b',
            r'\bAND\b.*\b1=1\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potential SQL injection detected in query: {v}")
        
        return v

class AgentExecuteRequest(BaseModel):
    task: str = Field(
        ..., 
        description="Task to execute",
        min_length=1,
        max_length=500
    )
    agent_type: str = Field(
        ..., 
        description="Type of agent to use",
        pattern=r'^(mcp|database|general)$'


    )
    context: Optional[Dict[str, Any]] = None
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        valid_types = ['mcp', 'database']
        if v not in valid_types:
            raise ValueError(f"Invalid agent type, must be one of: {valid_types}")
        return v

class ChatRequest(BaseModel):
    message: str = Field(
        ..., 
        description="User's chat message",
        min_length=1,
        max_length=1000
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID for multi-turn conversations",
        max_length=100
    )
    context: Optional[Dict[str, Any]] = None
