from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ModelScope 配置
    modelscope_api_key: str
    modelscope_api_base: str
    modelscope_model_id: str
    
    # 数据库配置
    database_url: str
    
    # MCP 服务配置
    mcp_server_url: str
    
    # 日志配置
    log_level: str
    
    # FastAPI 应用配置
    app_title: str
    app_description: str
    app_version: str
    
    # 服务器配置
    server_host: str
    server_port: int
    server_reload: bool
    
    # Agent 配置
    agent_temperature: float
    agent_max_iterations: int
    
    # 数据库工具配置
    db_tool_name: str
    db_tool_description: str
    db_query_limit: int
    db_query_max_length: int
    
    # MCP 工具配置
    mcp_tool_name: str
    mcp_tool_description: str
    mcp_request_timeout: float
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
