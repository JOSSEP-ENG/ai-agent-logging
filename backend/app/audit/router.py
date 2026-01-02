from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db, AuditStatus
from app.audit.service import AuditService


router = APIRouter(prefix="/api/audit", tags=["Audit"])


# ============ Pydantic 스키마 ============

class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""
    id: UUID
    timestamp: datetime
    user_id: str
    session_id: Optional[UUID] = None
    user_query: Optional[str] = None
    tool_name: str
    tool_params: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    status: AuditStatus
    error_message: Optional[str] = None
    execution_time_ms: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """감사 로그 목록 응답"""
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(BaseModel):
    """감사 로그 통계 응답"""
    total: int
    success: int
    fail: int
    denied: int
    by_tool: Dict[str, int]


# ============ API 엔드포인트 ============

@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    tool_name: Optional[str] = Query(None, description="Tool 이름 필터"),
    keyword: Optional[str] = Query(None, description="응답 내 키워드 검색"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    db: AsyncSession = Depends(get_db),
):
    """감사 로그 목록 조회
    
    필터 옵션:
    - user_id: 특정 사용자의 로그만 조회
    - tool_name: 특정 Tool 호출 로그만 조회
    - keyword: 응답 JSON 내 텍스트 검색 (예: "C001")
    - start_date, end_date: 기간 필터
    """
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
    
    return AuditLogListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=len(logs),  # TODO: 실제 전체 개수 쿼리
        limit=limit,
        offset=offset,
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """감사 로그 상세 조회 (원본 JSON 포함)"""
    service = AuditService(db)
    log = await service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="로그를 찾을 수 없습니다")
    
    return AuditLogResponse.model_validate(log)


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
):
    """감사 로그 통계 조회
    
    - 전체 호출 수
    - 성공/실패/거부 수
    - Tool별 호출 수
    """
    service = AuditService(db)
    stats = await service.get_stats(start_date=start_date, end_date=end_date)
    
    return AuditStatsResponse(**stats)
