from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import re

class AgentResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MCPToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    
    @field_validator('tool_name')
    def validate_tool_name(cls, v):
        # 限制工具名称格式
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Tool name can only contain letters, numbers, underscores, and hyphens")
        
        # 限制工具名称长度
        if len(v) > 50:
            raise ValueError("Tool name too long, maximum length is 50 characters")
        return v
    
    @field_validator('parameters')
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
    query: str = Field(..., description="SQL query to execute")
    params: Optional[Dict[str, Any]] = None
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum number of rows to return")
    
    @field_validator('query')
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
            r';',
            r'\bOR\b.*\b1=1\b',
            r'\bAND\b.*\b1=1\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Potential SQL injection detected in query: {v}")
        
        # 限制查询长度
        if len(v) > 1000:
            raise ValueError("Query too long, maximum length is 1000 characters")
        
        return v

class AgentExecuteRequest(BaseModel):
    task: str = Field(..., description="Task to execute")
    agent_type: str = Field(..., description="Type of agent to use")
    context: Optional[Dict[str, Any]] = None
    
    @field_validator('agent_type')
    def validate_agent_type(cls, v):
        valid_types = ['mcp', 'database']
        if v not in valid_types:
            raise ValueError(f"Invalid agent type, must be one of: {valid_types}")
        return v
    
    @field_validator('task')
    def validate_task(cls, v):
        # 限制任务长度
        if len(v) > 500:
            raise ValueError("Task too long, maximum length is 500 characters")
        return v
