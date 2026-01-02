import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum
from app.models.database import Base


class AuditStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    DENIED = "denied"


class AuditLog(Base):
    """감사 로그 테이블
    
    모든 MCP Tool 호출을 기록합니다.
    단순화 방식: response 필드에 전체 응답 JSON 저장
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # 사용자 정보
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # 요청 정보
    user_query = Column(Text, nullable=True)  # 사용자 자연어 원문
    tool_name = Column(String(255), nullable=False, index=True)  # 호출된 MCP Tool
    tool_params = Column(JSONB, nullable=True)  # Tool에 전달된 파라미터
    
    # 응답 정보 (단순화 방식: 전체 저장)
    response = Column(JSONB, nullable=True)  # MCP 응답 전체
    
    # 상태
    status = Column(SQLEnum(AuditStatus), nullable=False, default=AuditStatus.SUCCESS)
    error_message = Column(Text, nullable=True)
    
    # 메타데이터
    execution_time_ms = Column(String(50), nullable=True)  # 실행 시간
    
    def __repr__(self):
        return f"<AuditLog {self.id} | {self.user_id} | {self.tool_name}>"
