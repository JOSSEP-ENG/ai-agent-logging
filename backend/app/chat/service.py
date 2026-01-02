"""대화 관리 서비스

세션 생성/조회, 메시지 저장/조회를 담당합니다.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage


class ChatService:
    """대화 관리 서비스
    
    세션 기반으로 대화를 관리합니다.
    - 세션 ID로 대화 완전 분리
    - 최근 N개 메시지만 LLM에 전달 (토큰 절약)
    """
    
    MAX_HISTORY_MESSAGES = 20  # LLM에 전달할 최대 메시지 수
    MAX_HISTORY_TOKENS = 4000  # 최대 토큰 수 (향후 구현)
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ 세션 관리 ============
    
    async def create_session(
        self,
        user_id: str,
        title: Optional[str] = None,
    ) -> ChatSession:
        """새 대화 세션 생성"""
        session = ChatSession(
            user_id=user_id,
            title=title or "새 대화",
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """세션 조회
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID (권한 확인용)
        """
        query = select(ChatSession).where(ChatSession.id == session_id)
        
        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_session_with_messages(
        self,
        session_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """세션 + 메시지 함께 조회"""
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        
        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[ChatSession]:
        """사용자의 세션 목록 조회"""
        query = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
        )
        
        if active_only:
            query = query.where(ChatSession.is_active == True)
        
        query = (
            query
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_session_title(
        self,
        session_id: uuid.UUID,
        title: str,
    ) -> Optional[ChatSession]:
        """세션 제목 업데이트"""
        session = await self.get_session(session_id)
        
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(session)
        
        return session
    
    async def delete_session(
        self,
        session_id: uuid.UUID,
        user_id: Optional[str] = None,
        soft_delete: bool = True,
    ) -> bool:
        """세션 삭제
        
        Args:
            soft_delete: True면 is_active=False, False면 실제 삭제
        """
        session = await self.get_session(session_id, user_id)
        
        if not session:
            return False
        
        if soft_delete:
            session.is_active = False
            await self.db.commit()
        else:
            await self.db.delete(session)
            await self.db.commit()
        
        return True
    
    # ============ 메시지 관리 ============
    
    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        token_count: Optional[int] = None,
    ) -> ChatMessage:
        """메시지 추가"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            token_count=token_count,
        )
        
        self.db.add(message)
        
        # 세션 updated_at 갱신
        session = await self.get_session(session_id)
        if session:
            session.updated_at = datetime.utcnow()
            
            # 첫 메시지면 제목 자동 생성
            if not session.title or session.title == "새 대화":
                session.title = self._generate_title(content)
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_messages(
        self,
        session_id: uuid.UUID,
        limit: Optional[int] = None,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[ChatMessage]:
        """세션의 메시지 조회
        
        Args:
            limit: 최대 조회 개수
            before_id: 이 메시지 이전 것만 조회 (페이지네이션)
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
        )
        
        if before_id:
            # 특정 메시지 이전 것만
            subquery = select(ChatMessage.created_at).where(ChatMessage.id == before_id)
            query = query.where(ChatMessage.created_at < subquery.scalar_subquery())
        
        query = query.order_by(ChatMessage.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_messages(
        self,
        session_id: uuid.UUID,
        limit: int = None,
    ) -> List[ChatMessage]:
        """최근 N개 메시지 조회 (LLM 히스토리용)"""
        limit = limit or self.MAX_HISTORY_MESSAGES
        
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        # 시간순 정렬 (오래된 것 → 최신)
        return list(reversed(messages))
    
    async def get_message_count(self, session_id: uuid.UUID) -> int:
        """세션의 메시지 수"""
        from sqlalchemy import func
        
        query = (
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == session_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    # ============ 유틸리티 ============
    
    def _generate_title(self, first_message: str, max_length: int = 30) -> str:
        """첫 메시지로 대화 제목 생성"""
        # 첫 줄만 사용
        title = first_message.split('\n')[0].strip()
        
        # 길이 제한
        if len(title) > max_length:
            title = title[:max_length-3] + "..."
        
        return title or "새 대화"
    
    async def get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[uuid.UUID] = None,
    ) -> ChatSession:
        """세션 조회 또는 생성
        
        session_id가 주어지면 조회, 없으면 새로 생성
        """
        if session_id:
            session = await self.get_session(session_id, user_id)
            if session:
                return session
        
        # 새 세션 생성
        return await self.create_session(user_id)
