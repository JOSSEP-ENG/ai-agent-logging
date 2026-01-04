from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.audit.service import AuditService
from app.mcp_gateway.gateway import MCPGateway, MCPConnection, ToolCallResult
from app.mcp_gateway.mysql_client import MySQLMCPClient
from app.mcp_gateway.gateway_manager import UserGatewayManager
from app.config import get_settings


router = APIRouter(prefix="/api/mcp", tags=["MCP Gateway"])

# 싱글톤 Gateway Manager
_gateway_manager: Optional[UserGatewayManager] = None


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

def get_gateway_manager(db: AsyncSession = Depends(get_db)) -> UserGatewayManager:
    """Gateway Manager 싱글톤 가져오기"""
    global _gateway_manager

    if _gateway_manager is None:
        audit_service = AuditService(db)
        _gateway_manager = UserGatewayManager(audit_service)

    return _gateway_manager


# ============ API 엔드포인트 ============
# 참고: /connections 엔드포인트는 /api/mcp/connections로 이동되었습니다.

@router.get("/tools", response_model=List[ToolDefinitionResponse])
async def list_tools(
    current_user: User = Depends(get_current_user),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
    db: AsyncSession = Depends(get_db),
):
    """사용 가능한 Tool 목록 조회

    Gemini API의 function declarations 형식으로 반환됩니다.
    사용자별로 등록한 MCP 연결의 도구만 반환됩니다.
    """
    # 사용자별 Gateway 가져오기
    user_gateway = await gateway_manager.get_user_gateway(current_user.id, db)

    tools = user_gateway.get_all_tools()
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
    current_user: User = Depends(get_current_user),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
    db: AsyncSession = Depends(get_db),
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
    # 사용자별 Gateway 가져오기
    user_gateway = await gateway_manager.get_user_gateway(current_user.id, db)

    # Tool 호출
    result = await user_gateway.call_tool(
        tool_name=request.tool_name,
        params=request.params,
        user_id=str(current_user.id),
        user_query=request.user_query,
        session_id=request.session_id,
    )

    return ToolCallResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
    )
