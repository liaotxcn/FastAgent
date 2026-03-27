from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.models.schemas import AgentResponse, AgentExecuteRequest, MCPToolRequest, DatabaseQueryRequest, ChatRequest
from app.agent.mcp_agent import MCPAgent
from app.agent.db_agent import DatabaseAgent
from app.agent.router_agent import RouterAgent
from loguru import logger

router = APIRouter(prefix="/api/v1", tags=["agents"])

@router.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(request: AgentExecuteRequest):
    try:
        if request.agent_type == "mcp":
            agent = MCPAgent()
        elif request.agent_type == "database":
            agent = DatabaseAgent()
        else:
            return AgentResponse(
                success=False,
                message="Unknown agent type",
                data={
                    "input": request.task,
                    "output": ""
                },
                error=f"Unknown agent type: {request.agent_type}"
            )
        
        result = await agent.execute(request.task, request.context)
        return AgentResponse(**result)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return AgentResponse(
            success=False,
            message="Validation error",
            data={
                "input": request.task if hasattr(request, 'task') else "",
                "output": ""
            },
            error=str(e)
        )
    except Exception as e:
        logger.exception(f"Task execution failed: {e}")
        return AgentResponse(
            success=False,
            message="Task execution failed",
            data={
                "input": request.task if hasattr(request, 'task') else "",
                "output": ""
            },
            error=str(e)
        )

@router.post("/agent/mcp/tool", response_model=AgentResponse)
async def execute_mcp_tool(request: MCPToolRequest):
    from app.tools.mcp_tools import MCPToolWrapper
    
    tool = MCPToolWrapper()
    result = await tool._arun(request.tool_name, request.parameters)
    
    return AgentResponse(
        success=True,
        message="MCP tool executed",
        data={
            "input": f"Tool: {request.tool_name}, Params: {request.parameters}",
            "output": result
        },
        error=None
    )

@router.post("/agent/database/query", response_model=AgentResponse)
async def execute_database_query(request: DatabaseQueryRequest):
    from app.tools.db_tools import DatabaseQueryTool
    
    tool = DatabaseQueryTool()
    result = await tool._arun(request.query, request.params, request.limit)
    
    return AgentResponse(
        success=True,
        message="Database query executed",
        data={
            "input": request.query,
            "output": result
        },
        error=None
    )

@router.post("/agent/chat", response_model=AgentResponse)
async def smart_chat(request: ChatRequest):
    try:
        router_agent = RouterAgent()
        result = await router_agent.execute(request.message, request.context)
        return AgentResponse(**result)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return AgentResponse(
            success=False,
            message="Validation error",
            data={"input": request.message, "output": ""},
            error=str(e)
        )
    except Exception as e:
        logger.exception(f"Chat execution failed: {e}")
        return AgentResponse(
            success=False,
            message="Chat execution failed",
            data={"input": request.message, "output": ""},
            error=str(e)
        )

@router.get("/agent/health")
async def health_check():
    return AgentResponse(
        success=True,
        message="Agent system is healthy",
        data={
            "input": "Health check",
            "output": "Agent system is running",
            "status": "running"
        },
        error=None
    )