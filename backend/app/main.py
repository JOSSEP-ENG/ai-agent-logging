from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import init_db
from app.audit import audit_router
from app.mcp_gateway import mcp_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트"""
    # 시작 시: DB 테이블 생성
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # 종료 시: 정리 작업
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="MCP 기반 감사 로깅 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (기본)
app.include_router(audit_router)
app.include_router(mcp_router)

# MCP Connections 라우터
try:
    from app.mcp_gateway.router_connections import router as mcp_connections_router
    app.include_router(mcp_connections_router)
    print("✅ MCP Connections router loaded")
except Exception as e:
    print(f"⚠️ MCP Connections router failed: {e}")

# Agent 라우터 (Gemini 의존성 - 선택적)
try:
    from app.agent import agent_router
    app.include_router(agent_router)
    print("✅ Agent router loaded")
except Exception as e:
    print(f"⚠️ Agent router failed: {e}")

# Chat 라우터
try:
    from app.chat import chat_router, chat_auth_router
    app.include_router(chat_router)
    app.include_router(chat_auth_router)
    print("✅ Chat router loaded")
except Exception as e:
    print(f"⚠️ Chat router failed: {e}")

# Auth 라우터
try:
    from app.auth import auth_router
    app.include_router(auth_router)
    print("✅ Auth router loaded")
except Exception as e:
    print(f"⚠️ Auth router failed: {e}")

# Admin 라우터
try:
    from app.admin import admin_router
    app.include_router(admin_router)
    print("✅ Admin router loaded")
except Exception as e:
    print(f"⚠️ Admin router failed: {e}")


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """상세 헬스 체크"""
    return {
        "status": "healthy",
        "database": "connected",
        "mcp_gateway": "ready",
    }
