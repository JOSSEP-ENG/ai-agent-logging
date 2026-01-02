"""AI Agent 모듈

Gemini API와 MCP Gateway를 연결하여 사용자 질문을 처리합니다.
"""
from .service import AgentService, SimpleAgentService, Message, AgentResponse
from .router import router as agent_router

__all__ = [
    "AgentService",
    "SimpleAgentService", 
    "Message",
    "AgentResponse",
    "agent_router",
]

# GeminiClient는 선택적 import (API 키 없을 때 에러 방지)
try:
    from .gemini_client import GeminiClient, GeminiResponse, FunctionCall
    __all__.extend(["GeminiClient", "GeminiResponse", "FunctionCall"])
except ImportError:
    pass
