"""관리자 대시보드 서비스

시스템 통계 및 모니터링 기능을 제공합니다.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.audit import AuditLog, AuditStatus
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User, UserRole


class AdminService:
    """관리자 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ 대시보드 통계 ============
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """대시보드 전체 통계"""
        return {
            "users": await self._get_user_stats(),
            "sessions": await self._get_session_stats(),
            "audit": await self._get_audit_stats(),
            "system": await self._get_system_stats(),
        }
    
    async def _get_user_stats(self) -> Dict[str, Any]:
        """사용자 통계"""
        # 전체 사용자 수
        total_result = await self.db.execute(
            select(func.count(User.id))
        )
        total = total_result.scalar() or 0
        
        # 활성 사용자 수
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active = active_result.scalar() or 0
        
        # 역할별 사용자 수
        role_counts = {}
        for role in UserRole:
            result = await self.db.execute(
                select(func.count(User.id)).where(User.role == role)
            )
            role_counts[role.value] = result.scalar() or 0
        
        # 최근 7일 가입자 수
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        new_users = new_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_role": role_counts,
            "new_last_7_days": new_users,
        }
    
    async def _get_session_stats(self) -> Dict[str, Any]:
        """대화 세션 통계"""
        # 전체 세션 수
        total_result = await self.db.execute(
            select(func.count(ChatSession.id))
        )
        total = total_result.scalar() or 0
        
        # 활성 세션 수
        active_result = await self.db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.is_active == True)
        )
        active = active_result.scalar() or 0
        
        # 전체 메시지 수
        msg_result = await self.db.execute(
            select(func.count(ChatMessage.id))
        )
        total_messages = msg_result.scalar() or 0
        
        # 오늘 생성된 세션
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.created_at >= today_start)
        )
        today_sessions = today_result.scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "total_messages": total_messages,
            "today_sessions": today_sessions,
            "avg_messages_per_session": round(total_messages / total, 1) if total > 0 else 0,
        }
    
    async def _get_audit_stats(self) -> Dict[str, Any]:
        """감사 로그 통계"""
        # 전체 로그 수
        total_result = await self.db.execute(
            select(func.count(AuditLog.id))
        )
        total = total_result.scalar() or 0
        
        # 상태별 로그 수
        status_counts = {}
        for status in AuditStatus:
            result = await self.db.execute(
                select(func.count(AuditLog.id)).where(AuditLog.status == status)
            )
            status_counts[status.value] = result.scalar() or 0
        
        # 오늘 로그 수
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.timestamp >= today_start)
        )
        today_logs = today_result.scalar() or 0
        
        # Tool별 호출 수 (상위 5개)
        tool_result = await self.db.execute(
            select(AuditLog.tool_name, func.count(AuditLog.id).label('count'))
            .group_by(AuditLog.tool_name)
            .order_by(func.count(AuditLog.id).desc())
            .limit(5)
        )
        top_tools = [{"tool": row[0], "count": row[1]} for row in tool_result.all()]
        
        return {
            "total": total,
            "by_status": status_counts,
            "today_logs": today_logs,
            "top_tools": top_tools,
            "success_rate": round(status_counts.get("success", 0) / total * 100, 1) if total > 0 else 0,
        }
    
    async def _get_system_stats(self) -> Dict[str, Any]:
        """시스템 상태"""
        return {
            "status": "healthy",
            "database": "connected",
            "uptime": "N/A",  # 실제로는 서버 시작 시간 추적
        }
    
    # ============ 일별 통계 ============
    
    async def get_daily_stats(
        self,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """일별 통계 (최근 N일)"""
        stats = []
        
        for i in range(days - 1, -1, -1):
            date = datetime.utcnow().date() - timedelta(days=i)
            day_start = datetime.combine(date, datetime.min.time())
            day_end = datetime.combine(date, datetime.max.time())
            
            # 해당 일 로그 수
            log_result = await self.db.execute(
                select(func.count(AuditLog.id)).where(
                    and_(
                        AuditLog.timestamp >= day_start,
                        AuditLog.timestamp <= day_end,
                    )
                )
            )
            log_count = log_result.scalar() or 0
            
            # 해당 일 세션 수
            session_result = await self.db.execute(
                select(func.count(ChatSession.id)).where(
                    and_(
                        ChatSession.created_at >= day_start,
                        ChatSession.created_at <= day_end,
                    )
                )
            )
            session_count = session_result.scalar() or 0
            
            # 해당 일 신규 사용자 수
            user_result = await self.db.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.created_at >= day_start,
                        User.created_at <= day_end,
                    )
                )
            )
            user_count = user_result.scalar() or 0
            
            stats.append({
                "date": date.isoformat(),
                "audit_logs": log_count,
                "sessions": session_count,
                "new_users": user_count,
            })
        
        return stats
    
    # ============ 사용자별 통계 ============
    
    async def get_user_activity(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """사용자별 활동 통계"""
        # 사용자별 Tool 호출 수
        result = await self.db.execute(
            select(AuditLog.user_id, func.count(AuditLog.id).label('count'))
            .group_by(AuditLog.user_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(limit)
        )
        
        user_stats = []
        for row in result.all():
            user_id = row[0]
            call_count = row[1]
            
            # 사용자 정보 조회 (있는 경우)
            user_info = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_info.scalar_one_or_none()
            
            user_stats.append({
                "user_id": str(user_id),
                "email": user.email if user else "Unknown",
                "name": user.name if user else "Unknown",
                "tool_calls": call_count,
            })
        
        return user_stats
