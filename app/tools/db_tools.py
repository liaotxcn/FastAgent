from langchain.tools import BaseTool
from typing import Type, Optional, Annotated
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db
from app.config import settings
from loguru import logger
import re

class DatabaseQueryInput(BaseModel):
    query: Annotated[str, Field(
        description="SQL query to execute",
        min_length=5
    )]
    params: Optional[dict] = Field(default=None, description="Query parameters")
    limit: Optional[Annotated[int, Field(
        ge=1, 
        le=1000,
        description="Maximum number of rows to return"
    )]] = None
    
    @field_validator('query')
    @classmethod
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
        
        # 限制查询长度
        if len(v) > settings.db_query_max_length:
            raise ValueError(f"Query too long, maximum length is {settings.db_query_max_length} characters")
        
        return v

class DatabaseQueryTool(BaseTool):
    name: str = settings.db_tool_name
    description: str = settings.db_tool_description
    args_schema: Type[BaseModel] = DatabaseQueryInput
    
    async def _arun(self, query: str, params: Optional[dict] = None, limit: int = None) -> str:
        logger.info(f"Executing database query: {query[:100]}...")
        
        actual_limit = limit if limit is not None else settings.db_query_limit
        async for session in get_db():
            try:
                result = await session.execute(text(query), params or {})
                # 限制返回结果的行数
                rows = result.fetchmany(actual_limit) or []
                columns = result.keys() or []
                
                formatted_results = []
                for row in rows:
                    formatted_results.append(dict(zip(columns, row)))
                
                logger.info(f"Query executed successfully, returned {len(rows)} rows")
                # 如果结果被截断，添加提示信息
                if len(rows) == actual_limit:
                    return f"Query executed successfully. Results (limited to {actual_limit} rows): {formatted_results}"
                else:
                    return f"Query executed successfully. Results: {formatted_results}"
            except Exception as e:
                logger.exception(f"Error executing query: {str(e)}")
                return f"Error executing query: {str(e)}"
    
    def _run(self, query: str, params: Optional[dict] = None, limit: int = None) -> str:
        """同步执行数据库查询"""
        logger.info(f"Synchronously executing database query: {query[:100]}...")
        import asyncio
        return asyncio.run(self._arun(query, params, limit))
