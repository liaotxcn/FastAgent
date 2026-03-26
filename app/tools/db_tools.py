from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db
import re

class DatabaseQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    params: Optional[dict] = Field(default=None, description="Query parameters")
    
    @field_validator('query')
    def validate_sql_query(cls, v):
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

class DatabaseQueryTool(BaseTool):
    name = "database_query"
    description = "Execute SQL queries on the database. Use this tool whenever you need to query database information. Example: 'SELECT * FROM user' to get all user information."
    args_schema: Type[BaseModel] = DatabaseQueryInput
    
    async def _arun(self, query: str, params: Optional[dict] = None) -> str:
        async for session in get_db():
            try:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                columns = result.keys()
                
                formatted_results = []
                for row in rows:
                    formatted_results.append(dict(zip(columns, row)))
                
                return f"Query executed successfully. Results: {formatted_results}"
            except Exception as e:
                return f"Error executing query: {str(e)}"
    
    def _run(self, query: str, params: Optional[dict] = None) -> str:
        import asyncio
        return asyncio.run(self._arun(query, params))
