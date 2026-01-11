"""관리자 API 라우터

대시보드, 통계, 시스템 설정 API
Admin 권한 필요
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User, UserRole
from app.models.mcp_tool_permission import PermissionType
from app.auth.dependencies import require_admin, require_auditor
from app.admin.service import AdminService
from app.mcp_gateway.permission_service import ToolPermissionService


router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============ Pydantic 스키마 ============

class UserStatsResponse(BaseModel):
    """사용자 통계"""
    total: int
    active: int
    inactive: int
    by_role: Dict[str, int]
    new_last_7_days: int


class SessionStatsResponse(BaseModel):
    """세션 통계"""
    total: int
    active: int
    total_messages: int
    today_sessions: int
    avg_messages_per_session: float


class AuditStatsResponse(BaseModel):
    """감사 로그 통계"""
    total: int
    by_status: Dict[str, int]
    today_logs: int
    top_tools: List[Dict[str, Any]]
    success_rate: float


class SystemStatsResponse(BaseModel):
    """시스템 상태"""
    status: str
    database: str
    uptime: str


class DashboardResponse(BaseModel):
    """대시보드 전체 응답"""
    users: UserStatsResponse
    sessions: SessionStatsResponse
    audit: AuditStatsResponse
    system: SystemStatsResponse


class DailyStatResponse(BaseModel):
    """일별 통계"""
    date: str
    audit_logs: int
    sessions: int
    new_users: int


class UserActivityResponse(BaseModel):
    """사용자 활동"""
    user_id: str
    email: str
    name: str
    tool_calls: int


class MCPConnectionAdminResponse(BaseModel):
    """MCP 연결 정보 (Admin용)"""
    id: str
    name: str
    type: str
    enabled: bool
    tools_count: int
    created_by: Optional[str] = None


class SystemSettingResponse(BaseModel):
    """시스템 설정"""
    key: str
    value: Any
    description: str


class ToolPermissionResponse(BaseModel):
    """Tool 권한 응답"""
    id: str
    user_id: str
    connection_id: str
    tool_name: str
    permission_type: str
    param_constraints: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    created_at: str


class SetToolPermissionRequest(BaseModel):
    """Tool 권한 설정 요청"""
    connection_id: str
    tool_name: str
    permission_type: str  # "allowed" or "blocked"
    param_constraints: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None


class BulkSetPermissionsRequest(BaseModel):
    """일괄 권한 설정 요청"""
    connection_id: str
    tool_permissions: Dict[str, str]  # {tool_name: permission_type}


class ConnectionToolsResponse(BaseModel):
    """연결의 Tool 목록 응답"""
    connection_id: str
    connection_name: str
    tools: List[str]


# ============ 대시보드 API ============

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자 대시보드 통계
    
    전체 시스템 현황을 한눈에 파악할 수 있는 통계를 제공합니다.
    """
    service = AdminService(db)
    stats = await service.get_dashboard_stats()
    
    return DashboardResponse(
        users=UserStatsResponse(**stats["users"]),
        sessions=SessionStatsResponse(**stats["sessions"]),
        audit=AuditStatsResponse(**stats["audit"]),
        system=SystemStatsResponse(**stats["system"]),
    )


@router.get("/stats/daily", response_model=List[DailyStatResponse])
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="조회할 일 수"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """일별 통계
    
    최근 N일간의 일별 통계를 조회합니다.
    """
    service = AdminService(db)
    stats = await service.get_daily_stats(days=days)
    
    return [DailyStatResponse(**s) for s in stats]


@router.get("/stats/users", response_model=List[UserActivityResponse])
async def get_user_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자별 활동 통계
    
    Tool 호출 수 기준 상위 N명의 활동을 조회합니다.
    """
    service = AdminService(db)
    activities = await service.get_user_activity(limit=limit)
    
    return [UserActivityResponse(**a) for a in activities]


# ============ MCP 관리 API (Admin) ============

@router.get("/mcp/connections", response_model=List[MCPConnectionAdminResponse])
async def get_all_mcp_connections(
    current_user: User = Depends(require_admin),
):
    """전체 MCP 연결 목록 (Admin용)
    
    시스템에 등록된 모든 MCP 연결을 조회합니다.
    """
    # TODO: UserGatewayManager를 사용하여 모든 사용자의 연결 조회
    # 현재는 DB에서 직접 조회
    try:
        from app.mcp_gateway.connection_service import MCPConnectionService
        service = MCPConnectionService(db)
        # 모든 연결 조회 로직 필요 - 향후 구현
        return []  # 임시로 빈 배열 반환
    except Exception:
        return []


@router.post("/mcp/connections/{connection_id}/enable")
async def enable_mcp_connection(
    connection_id: str,
    current_user: User = Depends(require_admin),
):
    """MCP 연결 활성화"""
    from app.mcp_gateway.router import _gateway
    
    if _gateway is None or connection_id not in _gateway._connections:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    _gateway._connections[connection_id].enabled = True
    
    return {"message": "연결이 활성화되었습니다"}


@router.post("/mcp/connections/{connection_id}/disable")
async def disable_mcp_connection(
    connection_id: str,
    current_user: User = Depends(require_admin),
):
    """MCP 연결 비활성화"""
    from app.mcp_gateway.router import _gateway
    
    if _gateway is None or connection_id not in _gateway._connections:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    
    _gateway._connections[connection_id].enabled = False
    
    return {"message": "연결이 비활성화되었습니다"}


# ============ 감사 로그 관리 API (Auditor/Admin) ============

@router.get("/audit/logs")
async def get_all_audit_logs(
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    tool_name: Optional[str] = Query(None, description="Tool 이름 필터"),
    keyword: Optional[str] = Query(None, description="응답 내 키워드 검색"),
    status: Optional[str] = Query(None, description="상태 필터 (success/fail/denied)"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db),
):
    """전체 감사 로그 조회 (Auditor/Admin)
    
    시스템의 모든 감사 로그를 조회합니다.
    다양한 필터링 옵션을 제공합니다.
    """
    from app.audit.service import AuditService
    from app.models.audit import AuditStatus
    
    service = AuditService(db)
    logs = await service.get_logs(
        user_id=user_id,
        tool_name=tool_name,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "session_id": str(log.session_id) if log.session_id else None,
                "user_query": log.user_query,
                "tool_name": log.tool_name,
                "tool_params": log.tool_params,
                "response": log.response,
                "status": log.status.value,
                "error_message": log.error_message,
                "execution_time_ms": log.execution_time_ms,
            }
            for log in logs
        ],
        "total": len(logs),
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit/logs/{log_id}")
async def get_audit_log_detail(
    log_id: UUID,
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db),
):
    """감사 로그 상세 조회 (Auditor/Admin)"""
    from app.audit.service import AuditService
    
    service = AuditService(db)
    log = await service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="로그를 찾을 수 없습니다")
    
    return {
        "id": str(log.id),
        "timestamp": log.timestamp.isoformat(),
        "user_id": log.user_id,
        "session_id": str(log.session_id) if log.session_id else None,
        "user_query": log.user_query,
        "tool_name": log.tool_name,
        "tool_params": log.tool_params,
        "response": log.response,
        "status": log.status.value,
        "error_message": log.error_message,
        "execution_time_ms": log.execution_time_ms,
    }


@router.get("/audit/export")
async def export_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: User = Depends(require_auditor),
    db: AsyncSession = Depends(get_db),
):
    """감사 로그 내보내기 (Auditor/Admin)
    
    지정된 기간의 감사 로그를 JSON 또는 CSV 형식으로 내보냅니다.
    """
    from app.audit.service import AuditService
    import json
    
    service = AuditService(db)
    logs = await service.get_logs(
        start_date=start_date,
        end_date=end_date,
        limit=10000,  # 최대 10,000건
    )
    
    if format == "json":
        data = [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "tool_name": log.tool_name,
                "tool_params": log.tool_params,
                "status": log.status.value,
            }
            for log in logs
        ]
        return {"format": "json", "count": len(data), "data": data}
    
    elif format == "csv":
        # CSV 헤더
        lines = ["id,timestamp,user_id,tool_name,status"]
        for log in logs:
            lines.append(f"{log.id},{log.timestamp.isoformat()},{log.user_id},{log.tool_name},{log.status.value}")
        
        return {
            "format": "csv",
            "count": len(logs),
            "data": "\n".join(lines),
        }


# ============ 시스템 설정 API (Admin) ============

@router.get("/settings", response_model=List[SystemSettingResponse])
async def get_system_settings(
    current_user: User = Depends(require_admin),
):
    """시스템 설정 조회
    
    현재 시스템 설정값을 조회합니다.
    """
    from app.config import get_settings
    
    settings = get_settings()
    
    return [
        SystemSettingResponse(
            key="session_expire_hours",
            value=settings.session_expire_hours,
            description="세션 만료 시간 (시간)",
        ),
        SystemSettingResponse(
            key="audit_log_retention_days",
            value=settings.audit_log_retention_days,
            description="감사 로그 보존 기간 (일)",
        ),
        SystemSettingResponse(
            key="debug",
            value=settings.debug,
            description="디버그 모드",
        ),
        SystemSettingResponse(
            key="gemini_api_configured",
            value=bool(settings.gemini_api_key),
            description="Gemini API 키 설정 여부",
        ),
    ]


@router.get("/health/detailed")
async def get_detailed_health(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """상세 시스템 상태 (Admin)

    데이터베이스 연결, MCP 연결 등 상세 상태를 확인합니다.
    """
    from app.config import get_settings

    settings = get_settings()

    # DB 연결 확인
    db_status = "connected"
    try:
        await db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    # MCP 연결 확인
    mcp_status = {}
    try:
        from app.mcp_gateway.router import _gateway
        if _gateway:
            for conn_id, conn in _gateway._connections.items():
                mcp_status[conn.name] = "enabled" if conn.enabled else "disabled"
    except Exception:
        pass

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "gemini_api": "configured" if settings.gemini_api_key else "not_configured",
            "mcp_connections": mcp_status or "none",
        },
        "config": {
            "debug": settings.debug,
            "session_expire_hours": settings.session_expire_hours,
            "audit_log_retention_days": settings.audit_log_retention_days,
        },
    }


# ============ Tool 권한 관리 API (Admin) ============

@router.get("/mcp/permissions/{user_id}", response_model=List[ToolPermissionResponse])
async def get_user_tool_permissions(
    user_id: UUID,
    connection_id: Optional[UUID] = Query(None, description="특정 연결만 조회"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 Tool 권한 조회

    특정 사용자가 가진 모든 Tool 권한을 조회합니다.
    """
    service = ToolPermissionService(db)
    permissions = await service.get_user_permissions(user_id, connection_id)

    return [
        ToolPermissionResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            connection_id=str(p.connection_id),
            tool_name=p.tool_name,
            permission_type=p.permission_type.value,
            param_constraints=p.param_constraints,
            expires_at=p.expires_at.isoformat() if p.expires_at else None,
            created_at=p.created_at.isoformat(),
        )
        for p in permissions
    ]


@router.post("/mcp/permissions/{user_id}/tools", response_model=ToolPermissionResponse)
async def set_tool_permission(
    user_id: UUID,
    request: SetToolPermissionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Tool 권한 설정 (생성 또는 업데이트)

    사용자에게 특정 Tool에 대한 권한을 부여하거나 차단합니다.
    """
    service = ToolPermissionService(db)

    # permission_type 문자열을 Enum으로 변환
    try:
        permission_type = PermissionType(request.permission_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 권한 유형: {request.permission_type}. 'allowed' 또는 'blocked'를 사용하세요.",
        )

    # expires_at 문자열을 datetime으로 변환
    expires_at = None
    if request.expires_at:
        try:
            expires_at = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식")

    permission = await service.set_permission(
        user_id=user_id,
        connection_id=UUID(request.connection_id),
        tool_name=request.tool_name,
        permission_type=permission_type,
        created_by=current_user.id,
        param_constraints=request.param_constraints,
        expires_at=expires_at,
    )

    return ToolPermissionResponse(
        id=str(permission.id),
        user_id=str(permission.user_id),
        connection_id=str(permission.connection_id),
        tool_name=permission.tool_name,
        permission_type=permission.permission_type.value,
        param_constraints=permission.param_constraints,
        expires_at=permission.expires_at.isoformat() if permission.expires_at else None,
        created_at=permission.created_at.isoformat(),
    )


@router.post("/mcp/permissions/{user_id}/bulk", response_model=List[ToolPermissionResponse])
async def bulk_set_tool_permissions(
    user_id: UUID,
    request: BulkSetPermissionsRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """여러 Tool의 권한을 일괄 설정

    한 번의 요청으로 여러 Tool의 권한을 동시에 설정합니다.
    """
    service = ToolPermissionService(db)

    # permission_type 문자열을 Enum으로 변환
    tool_permissions = {}
    for tool_name, perm_str in request.tool_permissions.items():
        try:
            tool_permissions[tool_name] = PermissionType(perm_str)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"잘못된 권한 유형: {perm_str}",
            )

    permissions = await service.bulk_set_permissions(
        user_id=user_id,
        connection_id=UUID(request.connection_id),
        tool_permissions=tool_permissions,
        created_by=current_user.id,
    )

    return [
        ToolPermissionResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            connection_id=str(p.connection_id),
            tool_name=p.tool_name,
            permission_type=p.permission_type.value,
            param_constraints=p.param_constraints,
            expires_at=p.expires_at.isoformat() if p.expires_at else None,
            created_at=p.created_at.isoformat(),
        )
        for p in permissions
    ]


@router.delete("/mcp/permissions/{permission_id}")
async def delete_tool_permission(
    permission_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Tool 권한 삭제

    특정 Tool 권한을 삭제합니다.
    """
    service = ToolPermissionService(db)
    success = await service.delete_permission(permission_id)

    if not success:
        raise HTTPException(status_code=404, detail="권한을 찾을 수 없습니다")

    return {"message": "권한이 삭제되었습니다"}


@router.get("/mcp/connections/{connection_id}/tools", response_model=ConnectionToolsResponse)
async def get_connection_tools(
    connection_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """특정 MCP 연결의 Tool 목록 조회

    MCP 연결에서 사용 가능한 모든 Tool 목록을 반환합니다.
    """
    from app.mcp_gateway.connection_service import MCPConnectionService

    conn_service = MCPConnectionService(db)
    perm_service = ToolPermissionService(db)

    # 연결 정보 조회 (어떤 사용자의 연결이든 관리자는 조회 가능)
    # TODO: 실제로는 admin이므로 모든 연결 조회 가능하도록 수정 필요
    # 현재는 임시로 connection_id로만 조회
    from app.models.mcp_connection import MCPConnection
    from sqlalchemy import select

    query = select(MCPConnection).where(MCPConnection.id == connection_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")

    tools = await perm_service.get_connection_tools(connection_id)

    return ConnectionToolsResponse(
        connection_id=str(connection.id),
        connection_name=connection.name,
        tools=tools,
    )
