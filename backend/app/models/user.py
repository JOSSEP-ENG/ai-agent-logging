"""사용자 DB 모델

인증 및 권한 관리를 위한 사용자 모델입니다.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.models.database import Base


class UserRole(str, Enum):
    """사용자 역할
    
    - USER: 채팅, 본인 MCP 연결/해제, 본인 히스토리 조회
    - AUDITOR: User 권한 + 전체 감사 로그 조회
    - ADMIN: Auditor 권한 + 사용자 관리, MCP 설정, 시스템 설정
    """
    USER = "user"
    AUDITOR = "auditor"
    ADMIN = "admin"


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 인증 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 프로필
    name = Column(String(100), nullable=False)
    
    # 권한
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    
    # 상태
    is_active = Column(Boolean, default=True)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.email} | {self.role}>"
    
    def has_permission(self, required_role: UserRole) -> bool:
        """역할 기반 권한 확인
        
        ADMIN > AUDITOR > USER 순서로 상위 역할은 하위 권한 포함
        """
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.AUDITOR: 2,
            UserRole.ADMIN: 3,
        }
        
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
