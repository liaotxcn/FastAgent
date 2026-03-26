import asyncio
from app.database.connection import engine, Base
from app.database.models import AgentCallHistory

async def init_db():
    """初始化数据库表结构"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表结构初始化完成")

if __name__ == "__main__":
    asyncio.run(init_db())