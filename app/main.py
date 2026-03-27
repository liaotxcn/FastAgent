from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from loguru import logger

# 配置 Loguru 日志
logger.add("app.log", rotation="10 MB", level=settings.log_level)

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

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
