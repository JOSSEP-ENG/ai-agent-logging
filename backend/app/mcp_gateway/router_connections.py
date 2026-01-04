"""MCP 연결 관리 API

사용자가 자신의 MCP 서버 연결을 관리할 수 있는 API를 제공합니다.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.mcp_gateway.connection_service import MCPConnectionService
from app.mcp_gateway.gateway_manager import UserGatewayManager
from app.mcp_gateway.mysql_client import MySQLMCPClient
from app.audit.service import AuditService


router = APIRouter(prefix="/api/mcp/connections", tags=["MCP Connections"])

# 전역 Gateway Manager (싱글톤)
_gateway_manager: Optional[UserGatewayManager] = None


def get_gateway_manager(db: AsyncSession = Depends(get_db)):
    """Gateway Manager 싱글톤 가져오기"""
    global _gateway_manager
    if _gateway_manager is None:
        _gateway_manager = UserGatewayManager(AuditService(db))
    return _gateway_manager


# ============ Pydantic 스키마 ============

class CreateConnectionRequest(BaseModel):
    """MCP 연결 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255, description="연결 이름")
    type: str = Field(..., pattern="^(mysql|notion|google_calendar)$", description="연결 타입")
    description: Optional[str] = Field(None, description="연결 설명")
    config: Dict[str, Any] = Field(default_factory=dict, description="설정 정보")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="인증 정보 (암호화됨)")


class ConnectionResponse(BaseModel):
    """MCP 연결 응답"""
    id: UUID
    name: str
    type: str
    description: Optional[str]
    is_active: bool
    last_tested_at: Optional[datetime]
    last_test_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TestConnectionResponse(BaseModel):
    """연결 테스트 응답"""
    success: bool
    message: str
    tools_count: Optional[int] = None
    error: Optional[str] = None


# ============ API 엔드포인트 ============

@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    request: CreateConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """MCP 연결 생성

    새로운 MCP 서버 연결을 등록합니다.
    인증 정보는 자동으로 암호화되어 저장됩니다.
    """
    service = MCPConnectionService(db)

    try:
        connection = await service.create_connection(
            user_id=current_user.id,
            name=request.name,
            type=request.type,
            config=request.config,
            credentials=request.credentials,
            description=request.description,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"연결 생성 실패: {str(e)}",
        )

    # Gateway 재로드 (새 연결을 즉시 사용 가능하도록)
    await gateway_manager.reload_user_gateway(current_user.id, db)

    return ConnectionResponse(
        id=connection.id,
        name=connection.name,
        type=connection.type,
        description=connection.description,
        is_active=connection.is_active,
        last_tested_at=connection.last_tested_at,
        last_test_status=connection.last_test_status,
        created_at=connection.created_at,
    )


@router.get("", response_model=List[ConnectionResponse])
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 MCP 연결 목록 조회

    현재 사용자가 등록한 모든 MCP 연결을 조회합니다.
    """
    service = MCPConnectionService(db)
    connections = await service.get_user_connections(current_user.id, active_only=False)

    return [
        ConnectionResponse(
            id=conn.id,
            name=conn.name,
            type=conn.type,
            description=conn.description,
            is_active=conn.is_active,
            last_tested_at=conn.last_tested_at,
            last_test_status=conn.last_test_status,
            created_at=conn.created_at,
        )
        for conn in connections
    ]


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """MCP 연결 상세 조회

    특정 MCP 연결의 상세 정보를 조회합니다.
    """
    service = MCPConnectionService(db)
    connection = await service.get_connection(connection_id, current_user.id)

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연결을 찾을 수 없습니다",
        )

    return ConnectionResponse(
        id=connection.id,
        name=connection.name,
        type=connection.type,
        description=connection.description,
        is_active=connection.is_active,
        last_tested_at=connection.last_tested_at,
        last_test_status=connection.last_test_status,
        created_at=connection.created_at,
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """MCP 연결 삭제

    등록된 MCP 연결을 삭제합니다.
    """
    service = MCPConnectionService(db)
    success = await service.delete_connection(connection_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연결을 찾을 수 없습니다",
        )

    # Gateway 재로드
    await gateway_manager.reload_user_gateway(current_user.id, db)


@router.post("/{connection_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """MCP 연결 테스트

    등록된 연결이 정상적으로 작동하는지 테스트합니다.
    테스트 결과는 DB에 저장됩니다.
    """
    service = MCPConnectionService(db)
    connection = await service.get_connection(connection_id, current_user.id)

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연결을 찾을 수 없습니다",
        )

    # MySQL 연결 테스트
    if connection.type == "mysql":
        credentials = service.get_decrypted_credentials(connection)

        try:
            client = MySQLMCPClient(
                host=connection.config.get("host", "localhost"),
                port=connection.config.get("port", 3306),
                user=credentials.get("username", ""),
                password=credentials.get("password", ""),
                database=connection.config.get("database", ""),
                read_only=connection.config.get("read_only", True),
            )

            # 연결 시도
            connected = await client.connect()
            if not connected:
                await service.update_test_status(
                    connection_id,
                    current_user.id,
                    "failed",
                    "MySQL 서버에 연결할 수 없습니다",
                )

                return TestConnectionResponse(
                    success=False,
                    message="연결 실패",
                    error="MySQL 서버에 연결할 수 없습니다",
                )

            # Tool 목록 조회
            tools = await client.list_tools()

            # 연결 종료
            await client.disconnect()

            # 테스트 성공 저장
            await service.update_test_status(
                connection_id,
                current_user.id,
                "success",
                None,
            )

            return TestConnectionResponse(
                success=True,
                message="연결 성공",
                tools_count=len(tools),
            )

        except Exception as e:
            # 테스트 실패 저장
            await service.update_test_status(
                connection_id,
                current_user.id,
                "failed",
                str(e),
            )

            return TestConnectionResponse(
                success=False,
                message="연결 실패",
                error=str(e),
            )

    # 지원하지 않는 타입
    return TestConnectionResponse(
        success=False,
        message="지원하지 않는 연결 타입",
        error=f"Type '{connection.type}'은 현재 지원하지 않습니다",
    )
