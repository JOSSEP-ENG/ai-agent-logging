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
from app.auth.dependencies import require_admin, require_auditor
from app.admin.service import AdminService


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
