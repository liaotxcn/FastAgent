#!/usr/bin/env python3
"""初始化数据库表结构"""
import asyncio
from app.database.init_db import init_db

if __name__ == "__main__":
    asyncio.run(init_db())