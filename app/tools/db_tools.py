from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic.v1 import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db
from app.config import settings
import re

class DatabaseQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    params: Optional[dict] = Field(default=None, description="Query parameters")
    limit: Optional[int] = Field(default=None, ge=1, le=1000, description="Maximum number of rows to return")
    
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
        if len(v) > settings.db_query_max_length:
            raise ValueError(f"Query too long, maximum length is {settings.db_query_max_length} characters")
        
        return v

class DatabaseQueryTool(BaseTool):
    name = settings.db_tool_name
    description = settings.db_tool_description
    args_schema: Type[BaseModel] = DatabaseQueryInput
    
    async def _arun(self, query: str, params: Optional[dict] = None, limit: int = None) -> str:
        actual_limit = limit if limit is not None else settings.db_query_limit
        async for session in get_db():
            try:
                result = await session.execute(text(query), params or {})
                # 限制返回结果的行数
                rows = result.fetchmany(actual_limit)
                columns = result.keys()
                
                formatted_results = []
                for row in rows:
                    formatted_results.append(dict(zip(columns, row)))
                
                # 如果结果被截断，添加提示信息
                if len(rows) == actual_limit:
                    return f"Query executed successfully. Results (limited to {actual_limit} rows): {formatted_results}"
                else:
                    return f"Query executed successfully. Results: {formatted_results}"
            except Exception as e:
                return f"Error executing query: {str(e)}"
    
    def _run(self, query: str, params: Optional[dict] = None, limit: int = None) -> str:
        import asyncio
        return asyncio.run(self._arun(query, params, limit))
