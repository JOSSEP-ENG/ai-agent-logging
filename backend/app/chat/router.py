"""대화 관리 API 라우터

세션 기반 채팅 API를 제공합니다.
Agent와 통합되어 대화 히스토리를 자동으로 관리합니다.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.chat.service import ChatService
from app.mcp_gateway.router import get_gateway_manager
from app.mcp_gateway.gateway_manager import UserGatewayManager
from app.config import get_settings


router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ============ Pydantic 스키마 ============

class SessionCreateRequest(BaseModel):
    """세션 생성 요청"""
    title: Optional[str] = None


class SessionResponse(BaseModel):
    """세션 응답"""
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
    """세션 목록 응답"""
    sessions: List[SessionResponse]
    total: int


class MessageResponse(BaseModel):
    """메시지 응답"""
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    """세션 상세 응답 (메시지 포함)"""
    session: SessionResponse
    messages: List[MessageResponse]


class ChatMessageRequest(BaseModel):
    """채팅 메시지 요청"""
    message: str


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""
    user_message: MessageResponse
    assistant_message: MessageResponse
    tool_calls: List[Dict[str, Any]] = []
    execution_time_ms: int = 0


class SessionUpdateRequest(BaseModel):
    """세션 업데이트 요청"""
    title: str


# ============ 헬퍼 함수 ============

def get_current_user_id() -> str:
    """현재 사용자 ID
    
    인증이 적용되면 실제 user_id를 반환합니다.
    현재는 테스트용으로 "anonymous"를 반환합니다.
    
    TODO: 인증 미들웨어에서 request.state.user_id를 설정하도록 변경
    """
    return "anonymous"


# ============ 세션 API ============

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """새 대화 세션 생성"""
    user_id = get_current_user_id()
    service = ChatService(db)
    
    session = await service.create_session(
        user_id=user_id,
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
    db: AsyncSession = Depends(get_db),
):
    """세션 목록 조회"""
    user_id = get_current_user_id()
    service = ChatService(db)
    
    sessions = await service.get_user_sessions(
        user_id=user_id,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )
    
    # 메시지 수 조회
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
    db: AsyncSession = Depends(get_db),
):
    """세션 상세 조회 (메시지 포함)"""
    user_id = get_current_user_id()
    service = ChatService(db)
    
    session = await service.get_session_with_messages(session_id, user_id)
    
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


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    request: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """세션 제목 수정"""
    user_id = get_current_user_id()
    service = ChatService(db)
    
    # 권한 확인
    session = await service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    session = await service.update_session_title(session_id, request.title)
    msg_count = await service.get_message_count(session_id)
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        message_count=msg_count,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    permanent: bool = Query(False, description="영구 삭제 여부"),
    db: AsyncSession = Depends(get_db),
):
    """세션 삭제"""
    user_id = get_current_user_id()
    service = ChatService(db)
    
    success = await service.delete_session(
        session_id=session_id,
        user_id=user_id,
        soft_delete=not permanent,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    return {"message": "세션이 삭제되었습니다"}


# ============ 채팅 API (Agent 연동) ============

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: UUID,
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """세션에 메시지 전송 (AI 응답 포함)
    
    1. 사용자 메시지 저장
    2. 히스토리 로드
    3. Agent 호출
    4. AI 응답 저장
    5. 결과 반환
    """
    import time
    start_time = time.time()
    
    user_id = get_current_user_id()
    chat_service = ChatService(db)
    
    # 세션 확인
    session = await chat_service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    # 1. 사용자 메시지 저장
    user_msg = await chat_service.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    
    # 2. 히스토리 로드 (최근 N개)
    history_messages = await chat_service.get_recent_messages(
        session_id=session_id,
        limit=chat_service.MAX_HISTORY_MESSAGES,
    )
    
    # 3. Agent 호출
    from app.agent.service import Message, SimpleAgentService
    
    # 히스토리 변환
    history = [
        Message(role=msg.role, content=msg.content)
        for msg in history_messages[:-1]  # 현재 메시지 제외
    ]
    
    # Agent 서비스 가져오기
    settings = get_settings()
    if settings.gemini_api_key:
        try:
            from app.agent.gemini_client import GeminiClient
            from app.agent.service import AgentService
            gemini = GeminiClient(settings.gemini_api_key)
            agent = AgentService(gemini, gateway)
        except Exception:
            agent = SimpleAgentService(gateway)
    else:
        agent = SimpleAgentService(gateway)
    
    # Agent 실행
    response = await agent.process_message(
        user_message=request.message,
        user_id=user_id,
        session_id=session_id,
        history=history,
    )
    
    # 4. AI 응답 저장
    assistant_msg = await chat_service.add_message(
        session_id=session_id,
        role="assistant",
        content=response.message,
        tool_calls=response.tool_calls if response.tool_calls else None,
    )
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # 5. 결과 반환
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


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """세션의 메시지 목록 조회"""
    user_id = get_current_user_id()
    chat_service = ChatService(db)
    
    # 권한 확인
    session = await chat_service.get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    messages = await chat_service.get_messages(session_id, limit=limit)
    
    return [
        MessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            tool_calls=msg.tool_calls,
        )
        for msg in messages
    ]


# ============ 빠른 채팅 API ============

@router.post("/quick", response_model=ChatMessageResponse)
async def quick_chat(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """빠른 채팅 (세션 자동 생성)
    
    세션 없이 빠르게 질문할 때 사용합니다.
    새 세션이 자동으로 생성됩니다.
    """
    user_id = get_current_user_id()
    chat_service = ChatService(db)
    
    # 새 세션 생성
    session = await chat_service.create_session(user_id=user_id)
    
    # 메시지 전송 (위의 send_message 로직 재사용)
    import time
    start_time = time.time()
    
    # 사용자 메시지 저장
    user_msg = await chat_service.add_message(
        session_id=session.id,
        role="user",
        content=request.message,
    )
    
    # Agent 호출
    from app.agent.service import SimpleAgentService
    
    settings = get_settings()
    if settings.gemini_api_key:
        try:
            from app.agent.gemini_client import GeminiClient
            from app.agent.service import AgentService
            gemini = GeminiClient(settings.gemini_api_key)
            agent = AgentService(gemini, gateway)
        except Exception:
            agent = SimpleAgentService(gateway)
    else:
        agent = SimpleAgentService(gateway)
    
    response = await agent.process_message(
        user_message=request.message,
        user_id=user_id,
        session_id=session.id,
    )
    
    # AI 응답 저장
    assistant_msg = await chat_service.add_message(
        session_id=session.id,
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
