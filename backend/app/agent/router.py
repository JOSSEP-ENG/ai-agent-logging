"""AI Agent API 라우터

채팅 메시지를 처리하고 AI 응답을 반환합니다.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.audit.service import AuditService
from app.mcp_gateway.gateway_manager import UserGatewayManager
from app.mcp_gateway.router import get_gateway_manager
from app.agent.service import AgentService, SimpleAgentService, Message
from app.config import get_settings


router = APIRouter(prefix="/api/agent", tags=["AI Agent"])


# ============ Pydantic 스키마 ============

class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    session_id: Optional[UUID] = None
    history: Optional[List[ChatMessage]] = None


class ToolCallInfo(BaseModel):
    """Tool 호출 정보"""
    name: str
    args: Dict[str, Any] = {}
    result: Optional[Any] = None
    error: Optional[str] = None
    success: bool = True


class ChatResponse(BaseModel):
    """채팅 응답"""
    message: str
    tool_calls: List[ToolCallInfo] = []
    execution_time_ms: int = 0
    error: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Agent 상태 응답"""
    gemini_available: bool
    tools_count: int
    mode: str  # "gemini" or "simple"


# ============ 헬퍼 함수 ============

def get_agent_service(gateway_manager: UserGatewayManager = Depends(get_gateway_manager)):
    """Agent 서비스 인스턴스 반환"""
    settings = get_settings()
    
    # Gemini API 키가 있으면 Gemini Agent, 없으면 Simple Agent
    if settings.gemini_api_key:
        try:
            from app.agent.gemini_client import GeminiClient
            gemini = GeminiClient(settings.gemini_api_key)
            return AgentService(gemini, gateway)
        except Exception as e:
            print(f"Gemini 초기화 실패: {e}, Simple Agent 사용")
            return SimpleAgentService(gateway)
    else:
        return SimpleAgentService(gateway)


# ============ API 엔드포인트 ============

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """AI 채팅 메시지 처리
    
    사용자 메시지를 받아 AI가 처리하고 응답합니다.
    필요시 MCP Tool을 호출하여 데이터를 조회합니다.
    
    요청 예시:
    ```json
    {
        "message": "고객 목록 보여줘",
        "session_id": "uuid-optional",
        "history": [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 응답"}
        ]
    }
    ```
    """
    # TODO: 실제 인증된 사용자 ID 사용
    user_id = "test_user"
    
    # Agent 서비스 가져오기
    agent = get_agent_service(gateway)
    
    # 히스토리 변환
    history = None
    if request.history:
        history = [
            Message(role=msg.role, content=msg.content)
            for msg in request.history
        ]
    
    # 메시지 처리
    response = await agent.process_message(
        user_message=request.message,
        user_id=user_id,
        session_id=request.session_id,
        history=history,
    )
    
    # 응답 반환
    return ChatResponse(
        message=response.message,
        tool_calls=[
            ToolCallInfo(
                name=tc["name"],
                args=tc.get("args", {}),
                result=tc.get("result"),
                error=tc.get("error"),
                success=tc.get("success", True),
            )
            for tc in response.tool_calls
        ],
        execution_time_ms=response.execution_time_ms,
        error=response.error,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """스트리밍 채팅 응답 (향후 구현)
    
    Server-Sent Events로 실시간 응답을 반환합니다.
    현재는 전체 응답을 한 번에 반환합니다.
    """
    user_id = "test_user"
    agent = get_agent_service(gateway)
    
    async def generate():
        async for chunk in agent.process_message_stream(
            user_message=request.message,
            user_id=user_id,
            session_id=request.session_id,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """Agent 상태 확인
    
    Gemini API 연결 상태와 사용 가능한 Tool 수를 반환합니다.
    """
    settings = get_settings()
    
    gemini_available = bool(settings.gemini_api_key)
    tools = gateway.get_all_tools()
    
    return AgentStatusResponse(
        gemini_available=gemini_available,
        tools_count=len(tools),
        mode="gemini" if gemini_available else "simple",
    )


@router.post("/sync-tools")
async def sync_tools(
    gateway_manager: UserGatewayManager = Depends(get_gateway_manager),
):
    """Tool 목록 동기화
    
    MCP Gateway의 Tool 목록을 Gemini에 동기화합니다.
    새 MCP 연결 후 호출하세요.
    """
    settings = get_settings()
    
    if not settings.gemini_api_key:
        return {"message": "Simple 모드에서는 동기화가 필요 없습니다."}
    
    try:
        from app.agent.gemini_client import GeminiClient
        gemini = GeminiClient(settings.gemini_api_key)
        agent = AgentService(gemini, gateway)
        await agent.sync_tools()
        
        tools = gateway.get_all_tools()
        return {
            "message": f"{len(tools)}개의 Tool이 동기화되었습니다.",
            "tools": [t["name"] for t in tools],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
