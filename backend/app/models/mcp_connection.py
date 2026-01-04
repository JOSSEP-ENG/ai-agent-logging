"""MCP 연결 정보 모델

사용자별로 격리된 MCP 서버 연결 정보를 저장합니다.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.database import Base


class MCPConnection(Base):
    """MCP 연결 정보 테이블

    사용자가 등록한 데이터 소스 연결 정보를 저장합니다.
    - MySQL: 호스트, 포트, 계정 정보
    - Notion: OAuth 토큰
    - Google: OAuth 토큰
    """

    __tablename__ = "mcp_connections"

    # 기본 식별자
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 연결 메타데이터
    name = Column(String(255), nullable=False)  # 예: "Production MySQL"
    type = Column(String(50), nullable=False)  # 예: "mysql", "notion", "google"
    description = Column(Text, nullable=True)

    # 설정 정보 (JSONB로 유연하게 저장)
    # MySQL: {"host": "localhost", "port": 3306, "database": "mydb", "read_only": true}
    # Notion: {"workspace_id": "abc123", "database_id": "xyz789"}
    config = Column(JSONB, nullable=False, default={})

    # 보안: 암호화된 인증정보
    # MySQL: {"username": "root", "password": "1234"} -> 암호화
    # API Key: {"api_key": "sk-..."} -> 암호화
    encrypted_credentials = Column(Text, nullable=True)

    # OAuth 지원 (Phase 3)
    oauth_provider = Column(String(50), nullable=True)  # "notion", "google"
    oauth_access_token_encrypted = Column(Text, nullable=True)
    oauth_refresh_token_encrypted = Column(Text, nullable=True)
    oauth_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 연결 상태 추적
    is_active = Column(Boolean, default=True, nullable=False)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)  # "success" | "failed"
    last_test_error = Column(Text, nullable=True)

    # 감사 추적
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        # 같은 사용자가 같은 이름으로 중복 생성 불가
        Index("idx_mcp_connections_user_id", "user_id"),
        Index("uq_mcp_connections_user_name", "user_id", "name", unique=True),
    )

    def __repr__(self):
        return f"<MCPConnection(id={self.id}, user_id={self.user_id}, name={self.name}, type={self.type})>"
