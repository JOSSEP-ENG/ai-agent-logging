from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.audit.service import AuditService
from app.mcp_gateway.gateway import MCPGateway, MCPConnection, ToolCallResult
from app.mcp_gateway.mysql_client import MySQLMCPClient
from app.config import get_settings


router = APIRouter(prefix="/api/mcp", tags=["MCP Gateway"])

# 싱글톤 Gateway 인스턴스 (실제 운영에서는 DI 사용)
_gateway: Optional[MCPGateway] = None


# ============ Pydantic 스키마 ============

class MCPConnectionRequest(BaseModel):
    """MCP 연결 요청"""
    name: str
    type: str  # "mysql", "notion", etc.
    config: Dict[str, Any]


class MCPConnectionResponse(BaseModel):
    """MCP 연결 응답"""
    id: str
    name: str
    type: str
    enabled: bool


class ToolCallRequest(BaseModel):
    """Tool 호출 요청"""
    tool_name: str  # "mysql.query" 형식
    params: Dict[str, Any] = {}
    user_query: Optional[str] = None
    session_id: Optional[UUID] = None


class ToolCallResponse(BaseModel):
    """Tool 호출 응답"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0


class ToolDefinitionResponse(BaseModel):
    """Tool 정의 응답"""
    name: str
    description: str
    parameters: Dict[str, Any]


# ============ 헬퍼 함수 ============

async def get_gateway(db: AsyncSession = Depends(get_db)) -> MCPGateway:
    """Gateway 인스턴스 반환"""
    global _gateway
    
    if _gateway is None:
        audit_service = AuditService(db)
        _gateway = MCPGateway(audit_service)
    else:
        # DB 세션 업데이트
        _gateway.audit_service = AuditService(db)
    
    return _gateway


# ============ API 엔드포인트 ============

@router.post("/connections", response_model=MCPConnectionResponse)
async def create_connection(
    request: MCPConnectionRequest,
    gateway: MCPGateway = Depends(get_gateway),
):
    """MCP 연결 생성
    
    지원 타입:
    - mysql: MySQL 데이터베이스 연결
    
    MySQL 연결 예시:
    ```json
    {
        "name": "Production DB",
        "type": "mysql",
        "config": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "mydb"
        }
    }
    ```
    """
    import uuid as uuid_module
    
    connection_id = str(uuid_module.uuid4())
    
    if request.type == "mysql":
        # MySQL 클라이언트 생성
        client = MySQLMCPClient(
            host=request.config.get("host", "localhost"),
            port=request.config.get("port", 3306),
            user=request.config.get("user", "root"),
            password=request.config.get("password", ""),
            database=request.config.get("database", ""),
            read_only=request.config.get("read_only", True),
        )
        
        # 연결 시도
        connected = await client.connect()
        if not connected:
            raise HTTPException(
                status_code=400,
                detail="MySQL 연결 실패. 설정을 확인하세요.",
            )
        
        # Tool 목록 가져오기
        tools = await client.list_tools()
        
        # 연결 등록
        connection = MCPConnection(
            id=connection_id,
            name=request.name,
            type=request.type,
            config=request.config,
            enabled=True,
            tools=tools,
        )
        
        gateway.register_connection(connection, client)
        
        return MCPConnectionResponse(
            id=connection_id,
            name=request.name,
            type=request.type,
            enabled=True,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 MCP 타입: {request.type}",
        )


@router.get("/connections", response_model=List[MCPConnectionResponse])
async def list_connections(
    gateway: MCPGateway = Depends(get_gateway),
):
    """연결된 MCP 목록 조회"""
    connections = []
    for conn_id, conn in gateway._connections.items():
        connections.append(MCPConnectionResponse(
            id=conn.id,
            name=conn.name,
            type=conn.type,
            enabled=conn.enabled,
        ))
    return connections


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    gateway: MCPGateway = Depends(get_gateway),
):
    """MCP 연결 해제"""
    if connection_id not in gateway._connections:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    # 클라이언트 연결 해제
    client = gateway._clients.get(connection_id)
    if client:
        await client.disconnect()
    
    gateway.unregister_connection(connection_id)
    
    return {"message": "연결이 해제되었습니다"}


@router.get("/tools", response_model=List[ToolDefinitionResponse])
async def list_tools(
    gateway: MCPGateway = Depends(get_gateway),
):
    """사용 가능한 Tool 목록 조회
    
    Gemini API의 function declarations 형식으로 반환됩니다.
    """
    tools = gateway.get_all_tools()
    return [
        ToolDefinitionResponse(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
        )
        for tool in tools
    ]


@router.post("/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    gateway: MCPGateway = Depends(get_gateway),
):
    """Tool 호출 (감사 로깅 포함)
    
    Tool 이름은 "mcp_type.tool_name" 형식입니다.
    예: "mysql.query", "mysql.list_tables"
    
    요청 예시:
    ```json
    {
        "tool_name": "mysql.query",
        "params": {
            "sql": "SELECT * FROM customers LIMIT 10"
        },
        "user_query": "고객 목록 보여줘"
    }
    ```
    """
    # TODO: 실제 인증된 사용자 ID 사용
    user_id = "test_user"
    
    result = await gateway.call_tool(
        tool_name=request.tool_name,
        params=request.params,
        user_id=user_id,
        user_query=request.user_query,
        session_id=request.session_id,
    )
    
    return ToolCallResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
    )
