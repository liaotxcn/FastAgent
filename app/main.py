from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import redis
from app.config import settings
from app.api.routes import router, auth_router
from app.config import settings
from loguru import logger

# 配置 Loguru 日志
logger.add("app.log", rotation="10 MB", level=settings.log_level)

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 初始化 Redis 客户端
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# 自定义限流中间件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 基于 IP 限流
    ip = request.client.host
    key = f"rate_limit:{ip}"
    
    try:
        # 获取当前计数
        current = redis_client.get(key)
        if current:
            current = int(current)
            if current >= 10:  # 每分钟最多 10 个请求
                raise HTTPException(status_code=429, detail="Too Many Requests")
            # 增加计数
            redis_client.incr(key)
        else:
            # 设置初始值并过期时间
            redis_client.setex(key, 60, 1)  # 60秒过期
    except Exception as e:
        # Redis 错误时不影响请求
        pass
    
    response = await call_next(request)
    return response

app.include_router(router)
app.include_router(auth_router)

async def warmup_cache():
    """预热缓存"""
    try:
        # 1. 测试Redis连接
        redis_client.ping()
        
        # 2. 预热系统配置
        config_keys = [
            "app_title", "app_description", "app_version",
            "modelscope_model_id", "modelscope_api_base"
        ]
        for key in config_keys:
            value = getattr(settings, key, None)
            if value:
                redis_key = f"config:{key}"
                redis_client.setex(redis_key, 3600, str(value))
        
        # 3. 预热Agent描述信息
        from app.agent.registry import get_agent_descriptions
        agent_descriptions = get_agent_descriptions()
        if agent_descriptions:
            redis_client.setex("agent:descriptions", 3600, agent_descriptions)
        
        # 4. 预热工具列表
        from app.agent.general_agent import GeneralAgent
        from app.agent.db_agent import DatabaseAgent
        from app.agent.mcp_agent import MCPAgent
        
        agents = [GeneralAgent(), DatabaseAgent(), MCPAgent()]
        for agent in agents:
            tools = agent._get_tools()
            if tools:
                tool_names = [tool.name for tool in tools]
                agent_name = agent.__class__.__name__
                redis_client.setex(f"agent:{agent_name}:tools", 3600, str(tool_names))
        
        logger.info("缓存预热完成")
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("FastAgent system starting up...")
    await warmup_cache()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAgent system shutting down...")

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_title}",
        "version": settings.app_version,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload
    )
