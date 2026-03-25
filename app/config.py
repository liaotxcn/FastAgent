from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    modelscope_api_key: str
    modelscope_api_base: str
    modelscope_model_id: str
    database_url: str
    mcp_server_url: str
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
