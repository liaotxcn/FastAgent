from fastapi import APIRouter, HTTPException
from app.models.schemas import AgentResponse, AgentExecuteRequest, MCPToolRequest, DatabaseQueryRequest
from app.agent.mcp_agent import MCPAgent
from app.agent.db_agent import DatabaseAgent

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
                error=f"Unknown agent type: {request.agent_type}"
            )
        
        result = await agent.execute(request.task, request.context)
        return AgentResponse(**result)
    except Exception as e:
        return AgentResponse(
            success=False,
            message="Task execution failed",
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
        data={"result": result}
    )

@router.post("/agent/database/query", response_model=AgentResponse)
async def execute_database_query(request: DatabaseQueryRequest):
    from app.tools.db_tools import DatabaseQueryTool
    
    tool = DatabaseQueryTool()
    result = await tool._arun(request.query, request.params)
    
    return AgentResponse(
        success=True,
        message="Database query executed",
        data={"result": result}
    )

@router.get("/agent/health")
async def health_check():
    return AgentResponse(
        success=True,
        message="Agent system is healthy",
        data={"status": "running"}
    )
