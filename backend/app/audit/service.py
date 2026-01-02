import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import text

from app.models.audit import AuditLog, AuditStatus
from app.audit.masking import DataMasker


class AuditService:
    """감사 로깅 서비스
    
    모든 MCP Tool 호출에 대한 로그를 기록하고 조회합니다.
    단순화 방식: response 필드에 전체 응답 JSON 저장
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.masker = DataMasker()
    
    async def log_request(
        self,
        user_id: str,
        tool_name: str,
        tool_params: Optional[Dict[str, Any]] = None,
        user_query: Optional[str] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        """MCP 호출 전 로그 생성 (사전 로깅)
        
        Returns:
            AuditLog: 생성된 로그 객체 (나중에 응답 기록용)
        """
        # 파라미터 마스킹
        masked_params = self.masker.mask_response(tool_params) if tool_params else None
        
        log = AuditLog(
            user_id=user_id,
            tool_name=tool_name,
            tool_params=masked_params,
            user_query=user_query,
            session_id=session_id,
            status=AuditStatus.SUCCESS,  # 기본값, 나중에 업데이트
        )
        
        self.db.add(log)
        await self.db.flush()  # ID 생성을 위해 flush
        
        return log
    
    async def log_response(
        self,
        log_id: uuid.UUID,
        response: Any,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ) -> AuditLog:
        """MCP 호출 후 응답 기록 (사후 로깅)"""
        # 응답 마스킹
        masked_response = self.masker.mask_response(response)
        
        # 로그 조회 및 업데이트
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if log:
            log.response = masked_response
            log.status = status
            log.error_message = error_message
            if execution_time_ms:
                log.execution_time_ms = str(execution_time_ms)
            
            await self.db.commit()
        
        return log
    
    async def log_complete(
        self,
        user_id: str,
        tool_name: str,
        tool_params: Optional[Dict[str, Any]],
        response: Any,
        status: AuditStatus = AuditStatus.SUCCESS,
        user_query: Optional[str] = None,
        session_id: Optional[uuid.UUID] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ) -> AuditLog:
        """한 번에 전체 로그 기록 (간편 메서드)"""
        # 마스킹
        masked_params = self.masker.mask_response(tool_params) if tool_params else None
        masked_response = self.masker.mask_response(response)
        
        log = AuditLog(
            user_id=user_id,
            tool_name=tool_name,
            tool_params=masked_params,
            user_query=user_query,
            session_id=session_id,
            response=masked_response,
            status=status,
            error_message=error_message,
            execution_time_ms=str(execution_time_ms) if execution_time_ms else None,
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """감사 로그 조회 (필터링)
        
        Args:
            user_id: 사용자 ID 필터
            tool_name: Tool 이름 필터
            keyword: 응답 내 텍스트 검색 (LIKE)
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 조회 개수
            offset: 시작 위치
        """
        query = select(AuditLog)
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if tool_name:
            conditions.append(AuditLog.tool_name == tool_name)
        
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 키워드 검색 (response JSONB를 텍스트로 변환 후 검색)
        if keyword:
            query = query.where(
                AuditLog.response.cast(text("TEXT")).ilike(f"%{keyword}%")
            )
        
        query = query.order_by(AuditLog.timestamp.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_log_by_id(self, log_id: uuid.UUID) -> Optional[AuditLog]:
        """ID로 로그 상세 조회"""
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """감사 로그 통계"""
        conditions = []
        
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        # 전체 로그 수
        total_query = select(AuditLog)
        if conditions:
            total_query = total_query.where(and_(*conditions))
        
        total_result = await self.db.execute(total_query)
        logs = total_result.scalars().all()
        
        # 통계 계산
        total_count = len(logs)
        success_count = sum(1 for log in logs if log.status == AuditStatus.SUCCESS)
        fail_count = sum(1 for log in logs if log.status == AuditStatus.FAIL)
        denied_count = sum(1 for log in logs if log.status == AuditStatus.DENIED)
        
        # Tool별 호출 수
        tool_counts = {}
        for log in logs:
            tool_counts[log.tool_name] = tool_counts.get(log.tool_name, 0) + 1
        
        return {
            "total": total_count,
            "success": success_count,
            "fail": fail_count,
            "denied": denied_count,
            "by_tool": tool_counts,
        }
