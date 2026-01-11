"""MCP Tool 권한 관리 모델

사용자별 MCP Tool에 대한 세부 권한을 관리합니다.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum

from app.models.database import Base


class PermissionType(str, Enum):
    """권한 유형"""
    ALLOWED = "allowed"  # 허용
    BLOCKED = "blocked"  # 차단
    APPROVAL_REQUIRED = "approval_required"  # 승인 필요 (향후 구현)


class MCPToolPermission(Base):
    """MCP Tool 권한 테이블

    사용자별로 특정 MCP 서버의 특정 Tool에 대한 접근 권한을 관리합니다.

    예시:
    - user_id=alice, connection_id=mysql-prod, tool_name=read_query, permission=allowed
    - user_id=bob, connection_id=mysql-prod, tool_name=write_query, permission=blocked
    """

    __tablename__ = "mcp_tool_permissions"

    # 기본 식별자
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 사용자 및 연결 정보
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mcp_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tool 정보
    tool_name = Column(String(255), nullable=False)  # 예: "read_file", "write_file"

    # 권한 설정
    permission_type = Column(
        SQLEnum(PermissionType, name="permission_type_enum"),
        nullable=False,
        default=PermissionType.ALLOWED,
    )

    # 파라미터 제약 조건 (JSONB - Phase 2)
    # 예: {"path": {"allowed_prefixes": ["/home/user"], "blocked_patterns": ["/etc/*"]}}
    param_constraints = Column(JSONB, nullable=True)

    # 시간 기반 권한 (Phase 3)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 권한 만료 시간
    time_restrictions = Column(JSONB, nullable=True)
    # 예: {"allowed_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17]}
    # 예: {"allowed_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]}

    # Rate Limiting (Phase 4)
    rate_limit = Column(JSONB, nullable=True)
    # 예: {"max_calls_per_hour": 100, "max_calls_per_day": 500}

    # 메타데이터
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # 권한을 부여한 관리자

    __table_args__ = (
        # 같은 사용자가 같은 연결의 같은 Tool에 대해 중복 권한 생성 불가
        Index(
            "uq_mcp_tool_permissions_user_connection_tool",
            "user_id",
            "connection_id",
            "tool_name",
            unique=True,
        ),
        # 조회 성능을 위한 복합 인덱스
        Index("idx_mcp_tool_permissions_user_id", "user_id"),
        Index("idx_mcp_tool_permissions_connection_id", "connection_id"),
    )

    def __repr__(self):
        return (
            f"<MCPToolPermission("
            f"user_id={self.user_id}, "
            f"connection_id={self.connection_id}, "
            f"tool_name={self.tool_name}, "
            f"permission={self.permission_type.value}"
            f")>"
        )

    def is_expired(self) -> bool:
        """권한이 만료되었는지 확인"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_time_allowed(self, check_time: datetime = None) -> bool:
        """현재 시간이 허용된 시간대인지 확인

        Args:
            check_time: 확인할 시간 (None이면 현재 시간)

        Returns:
            시간 제약이 없거나 허용된 시간이면 True
        """
        if not self.time_restrictions:
            return True

        if check_time is None:
            check_time = datetime.utcnow()

        # 시간대 제약 확인
        if "allowed_hours" in self.time_restrictions:
            allowed_hours = self.time_restrictions["allowed_hours"]
            if check_time.hour not in allowed_hours:
                return False

        # 요일 제약 확인
        if "allowed_days" in self.time_restrictions:
            allowed_days = self.time_restrictions["allowed_days"]
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            current_day = day_names[check_time.weekday()]
            if current_day not in allowed_days:
                return False

        return True
