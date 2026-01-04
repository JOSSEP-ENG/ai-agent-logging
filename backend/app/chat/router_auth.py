"""인증된 대화 관리 API 라우터

인증이 필요한 세션 기반 채팅 API를 제공합니다.
/api/chat/auth/* 경로로 접근합니다.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User
from app.chat.service import ChatService
from app.mcp_gateway.router import get_gateway_manager
from app.mcp_gateway.gateway_manager import UserGatewayManager
from app.auth.dependencies import get_current_user
from app.config import get_settings


router = APIRouter(prefix="/api/chat/auth", tags=["Chat (Authenticated)"])


# ============ Pydantic 스키마 (chat/router.py와 공유) ============

class SessionResponse(BaseModel):
    id: UUID
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: List[MessageResponse]


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    tool_calls: List[Dict[str, Any]] = []
    execution_time_ms: int = 0


class SessionCreateRequest(BaseModel):
    title: Optional[str] = None


# ============ 인증된 세션 API ============

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """새 대화 세션 생성 (인증 필요)"""
    service = ChatService(db)
    
    session = await service.create_session(
        user_id=str(current_user.id),
        title=request.title,
    )
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        message_count=0,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 세션 목록 조회 (인증 필요)"""
    service = ChatService(db)
    
    sessions = await service.get_user_sessions(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
        active_only=active_only,
    )
    
    session_responses = []
    for session in sessions:
        msg_count = await service.get_message_count(session.id)
        session_responses.append(SessionResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=msg_count,
        ))
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses),
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """세션 상세 조회 (인증 필요, 본인 세션만)"""
    service = ChatService(db)
    
    session = await service.get_session_with_messages(
        session_id, 
        user_id=str(current_user.id),
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return SessionDetailResponse(
        session=SessionResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            is_active=session.is_active,
            message_count=len(session.messages),
        ),
        messages=[
            MessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                tool_calls=msg.tool_calls,
            )
            for msg in session.messages
        ],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """세션 삭제 (인증 필요, 본인 세션만)"""
    service = ChatService(db)
    
    success = await service.delete_session(
        session_id=session_id,
        user_id=str(current_user.id),
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return {"message": "세션이 삭제되었습니다"}


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """세션에 메시지 전송 (인증 필요)"""
    import time
    start_time = time.time()

    chat_service = ChatService(db)
    user_id = str(current_user.id)

    # 세션 확인 (본인 세션만)
    session = await chat_service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 사용자 메시지 저장
    user_msg = await chat_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
    )

    # 히스토리 로드
    history_messages = await chat_service.get_recent_messages(
        session_id=session_id,
        limit=chat_service.MAX_HISTORY_MESSAGES,
    )

    # 사용자별 Gateway 가져오기
    user_gateway = await gateway_manager.get_user_gateway(current_user.id, db)

    # Agent 호출
    from app.agent.service import Message, SimpleAgentService

    history = [
        Message(role=msg.role, content=msg.content)
        for msg in history_messages[:-1]
    ]

    settings = get_settings()
    if settings.gemini_api_key:
        try:
            from app.agent.gemini_client import GeminiClient
            from app.agent.service import AgentService
            gemini = GeminiClient(settings.gemini_api_key)
            agent = AgentService(gemini, user_gateway)
        except Exception:
            agent = SimpleAgentService(user_gateway)
    else:
        agent = SimpleAgentService(user_gateway)
    
    response = await agent.process_message(
        user_message=request.message,
        user_id=user_id,
        session_id=session_id,
        history=history,
    )
    
    # AI 응답 저장
    assistant_msg = await chat_service.add_message(
        session_id=session_id,
        role="assistant",
        content=response.message,
        tool_calls=response.tool_calls if response.tool_calls else None,
    )
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    return ChatMessageResponse(
        user_message=MessageResponse(
            id=user_msg.id,
            session_id=user_msg.session_id,
            role=user_msg.role,
            content=user_msg.content,
            created_at=user_msg.created_at,
            tool_calls=user_msg.tool_calls,
        ),
        assistant_message=MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            tool_calls=assistant_msg.tool_calls,
        ),
        tool_calls=response.tool_calls,
        execution_time_ms=execution_time_ms,
    )
