from typing import Dict, Any

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "database": {
        "class": "DatabaseAgent",
        "description": "处理数据库查询、数据检索、SQL操作相关的问题",
        "keywords": ["数据库", "查询", "数据", "表", "sql", "记录", "用户信息", "select"]
    },
    "mcp": {
        "class": "MCPAgent",
        "description": "处理MCP工具调用、外部服务集成相关的问题",
        "keywords": ["工具", "调用", "mcp", "外部服务", "api"]
    },
    "general": {
        "class": "GeneralAgent",
        "description": "处理一般性对话、问答、闲聊等不需要特定工具的问题",
        "keywords": ["你好", "是什么", "怎么", "为什么", "介绍", "帮助"]
    }
}

def get_agent_info(agent_type: str) -> Dict[str, Any]:
    return AGENT_REGISTRY.get(agent_type, AGENT_REGISTRY["general"])

def get_all_agent_types() -> list:
    return list(AGENT_REGISTRY.keys())

def get_agent_descriptions() -> str:
    return "\n".join([f"- {k}: {v['description']}" for k, v in AGENT_REGISTRY.items()])