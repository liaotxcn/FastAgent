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

@app.on_event("startup")
async def startup_event():
    logger.info("FastAgent system starting up...")

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
