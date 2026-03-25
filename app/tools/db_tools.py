from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db

class DatabaseQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    params: Optional[dict] = Field(default=None, description="Query parameters")

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
