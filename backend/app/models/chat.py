"""대화 관리 DB 모델

세션과 메시지를 저장합니다.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.database import Base


class ChatSession(Base):
    """대화 세션 테이블
    
    사용자별 대화 세션을 관리합니다.
    세션 ID로 대화를 완전히 분리합니다.
    """
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    
    # 세션 메타데이터
    title = Column(String(255), nullable=True)  # 대화 제목 (첫 메시지 기반 자동 생성)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 상태
    is_active = Column(Boolean, default=True)  # 활성 세션 여부
    
    # 관계
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")
    
    def __repr__(self):
        return f"<ChatSession {self.id} | {self.user_id}>"


class ChatMessage(Base):
    """대화 메시지 테이블
    
    세션 내 모든 메시지를 저장합니다.
    """
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # 메시지 내용
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Tool 호출 정보 (선택)
    tool_calls = Column(JSONB, nullable=True)  # Agent가 호출한 Tool 목록
    
    # 토큰 사용량 (향후 사용)
    token_count = Column(Integer, nullable=True)
    
    # 관계
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.id} | {self.role}>"
