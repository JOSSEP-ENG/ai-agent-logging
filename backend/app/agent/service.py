"""AI Agent 서비스

Gemini API와 MCP Gateway를 연결하여 사용자 질문을 처리합니다.

흐름:
1. 사용자 질문 수신
2. Gemini API에 질문 + Tool 목록 전달
3. Gemini가 function_call 응답 → MCP Gateway로 Tool 호출
4. Tool 결과 → Gemini API 재호출
5. 최종 응답 반환
"""
import uuid
import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime

from app.agent.gemini_client import GeminiClient, GeminiResponse, FunctionCall
from app.mcp_gateway.gateway import MCPGateway, ToolCallResult
from app.config import get_settings


@dataclass
class Message:
    """대화 메시지"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Agent 응답"""
    message: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: int = 0
    error: Optional[str] = None


class AgentService:
    """AI Agent 서비스
    
    사용자 질문을 받아 Gemini API와 MCP Gateway를 통해 처리합니다.
    
    특징:
    - LLM은 판단만, 실행은 백엔드가 담당
    - 모든 Tool 호출은 MCP Gateway를 통해 감사 로깅
    - 멀티턴 대화 지원 (최대 3회 Tool 호출)
    """
    
    MAX_TOOL_CALLS = 3  # 무한 루프 방지
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        mcp_gateway: MCPGateway,
    ):
        self.gemini = gemini_client
        self.gateway = mcp_gateway
        self._tools_synced = False
    
    async def sync_tools(self) -> None:
        """MCP Gateway의 Tool 목록을 Gemini에 동기화"""
        tools = self.gateway.get_all_tools()
        self.gemini.set_tools(tools)
        self._tools_synced = True
    
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[uuid.UUID] = None,
        history: Optional[List[Message]] = None,
    ) -> AgentResponse:
        """사용자 메시지 처리
        
        Args:
            user_message: 사용자 질문
            user_id: 사용자 ID (감사 로그용)
            session_id: 대화 세션 ID
            history: 이전 대화 내역 (최근 N개)
        
        Returns:
            AgentResponse: 최종 응답
        """
        import time
        start_time = time.time()
        
        # Tool 동기화 확인
        if not self._tools_synced:
            await self.sync_tools()
        
        # 대화 히스토리 구성
        messages = self._build_messages(history or [], user_message)
        
        # Tool 호출 추적
        all_tool_calls = []
        tool_call_count = 0
        
        try:
            # Gemini API 호출
            response = await self.gemini.generate(messages)
            
            # 멀티턴 처리: Tool 호출이 있으면 실행 후 재호출
            while response.function_calls and tool_call_count < self.MAX_TOOL_CALLS:
                tool_call_count += 1
                
                for func_call in response.function_calls:
                    # Tool 호출 실행
                    tool_result = await self._execute_tool(
                        func_call,
                        user_id=user_id,
                        user_query=user_message,
                        session_id=session_id,
                    )
                    
                    # 호출 정보 기록
                    all_tool_calls.append({
                        "name": func_call.name,
                        "args": func_call.args,
                        "result": tool_result.data if tool_result.success else None,
                        "error": tool_result.error,
                        "success": tool_result.success,
                    })
                    
                    # Tool 결과로 Gemini 재호출
                    if tool_result.success:
                        response = await self.gemini.generate_with_function_result(
                            messages=messages,
                            function_name=self.gemini.convert_tool_name_for_gemini(func_call.name),
                            function_result=tool_result.data,
                        )
                    else:
                        # Tool 실패 시 에러 메시지로 재호출
                        response = await self.gemini.generate_with_function_result(
                            messages=messages,
                            function_name=self.gemini.convert_tool_name_for_gemini(func_call.name),
                            function_result={"error": tool_result.error},
                        )
            
            # 최종 응답
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return AgentResponse(
                message=response.text or "응답을 생성할 수 없습니다.",
                tool_calls=all_tool_calls,
                execution_time_ms=execution_time_ms,
            )
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Rate Limit 에러 처리
            if "429" in error_msg or "quota" in error_msg.lower():
                return AgentResponse(
                    message="요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.",
                    tool_calls=all_tool_calls,
                    execution_time_ms=execution_time_ms,
                    error="RATE_LIMIT_EXCEEDED",
                )
            
            return AgentResponse(
                message=f"오류가 발생했습니다: {error_msg}",
                tool_calls=all_tool_calls,
                execution_time_ms=execution_time_ms,
                error=error_msg,
            )
    
    async def process_message_stream(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[uuid.UUID] = None,
        history: Optional[List[Message]] = None,
    ) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성 (향후 구현)
        
        현재는 전체 응답을 한 번에 반환합니다.
        향후 Gemini의 스트리밍 API를 활용하여 실시간 응답을 제공합니다.
        """
        response = await self.process_message(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            history=history,
        )
        
        yield response.message
    
    async def _execute_tool(
        self,
        func_call: FunctionCall,
        user_id: str,
        user_query: str,
        session_id: Optional[uuid.UUID] = None,
    ) -> ToolCallResult:
        """Tool 실행
        
        MCP Gateway를 통해 Tool을 호출합니다.
        감사 로깅은 Gateway에서 자동으로 수행됩니다.
        """
        return await self.gateway.call_tool(
            tool_name=func_call.name,
            params=func_call.args,
            user_id=user_id,
            user_query=user_query,
            session_id=session_id,
        )
    
    def _build_messages(
        self,
        history: List[Message],
        current_message: str,
    ) -> List[Dict[str, str]]:
        """Gemini API용 메시지 목록 구성
        
        히스토리와 현재 메시지를 결합합니다.
        토큰 제한을 고려하여 최근 N개만 포함합니다.
        """
        settings = get_settings()
        max_history = 20  # 최근 20개 메시지만
        
        messages = []
        
        # 히스토리 추가 (최근 N개)
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        for msg in recent_history:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        # 현재 메시지 추가
        messages.append({
            "role": "user",
            "content": current_message,
        })
        
        return messages


class SimpleAgentService:
    """간소화된 Agent 서비스 (Gemini API 없이 테스트용)
    
    Gemini API 키가 없을 때 기본적인 Tool 호출만 지원합니다.
    키워드 기반으로 Tool을 선택합니다.
    """
    
    KEYWORD_TOOL_MAP = {
        ("테이블", "목록", "리스트"): ("mysql.list_tables", {}),
        ("구조", "스키마", "컬럼"): ("mysql.describe_table", {"table": ""}),
        ("고객", "customers"): ("mysql.query", {"sql": "SELECT * FROM customers LIMIT 10"}),
        ("주문", "orders"): ("mysql.query", {"sql": "SELECT * FROM orders LIMIT 10"}),
        ("상품", "products"): ("mysql.query", {"sql": "SELECT * FROM products LIMIT 10"}),
    }
    
    def __init__(self, mcp_gateway: MCPGateway):
        self.gateway = mcp_gateway
    
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> AgentResponse:
        """키워드 기반 메시지 처리"""
        import time
        start_time = time.time()
        
        # 키워드 매칭
        tool_name, tool_params = self._match_tool(user_message.lower())
        
        if not tool_name:
            return AgentResponse(
                message="죄송합니다. 요청을 이해하지 못했습니다. '고객 목록', '테이블 목록', '주문 내역' 등을 물어보세요.",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        
        # describe_table인 경우 테이블 이름 추출
        if tool_name == "mysql.describe_table":
            table_name = self._extract_table_name(user_message)
            if table_name:
                tool_params = {"table": table_name}
            else:
                return AgentResponse(
                    message="어떤 테이블의 구조를 보여드릴까요? (예: customers 테이블 구조 보여줘)",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
        
        # Tool 호출
        result = await self.gateway.call_tool(
            tool_name=tool_name,
            params=tool_params,
            user_id=user_id,
            user_query=user_message,
            session_id=session_id,
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if result.success:
            # 결과 포맷팅
            formatted = self._format_result(tool_name, result.data)
            return AgentResponse(
                message=formatted,
                tool_calls=[{
                    "name": tool_name,
                    "args": tool_params,
                    "success": True,
                }],
                execution_time_ms=execution_time_ms,
            )
        else:
            return AgentResponse(
                message=f"오류가 발생했습니다: {result.error}",
                tool_calls=[{
                    "name": tool_name,
                    "args": tool_params,
                    "success": False,
                    "error": result.error,
                }],
                execution_time_ms=execution_time_ms,
                error=result.error,
            )
    
    def _match_tool(self, message: str) -> tuple:
        """키워드로 Tool 매칭"""
        for keywords, (tool_name, params) in self.KEYWORD_TOOL_MAP.items():
            if any(kw in message for kw in keywords):
                return tool_name, params.copy()
        return None, None
    
    def _extract_table_name(self, message: str) -> Optional[str]:
        """메시지에서 테이블 이름 추출"""
        known_tables = ["customers", "orders", "products"]
        message_lower = message.lower()
        
        for table in known_tables:
            if table in message_lower:
                return table
        
        return None
    
    def _format_result(self, tool_name: str, data: Any) -> str:
        """결과 포맷팅"""
        if not data:
            return "결과가 없습니다."
        
        if tool_name == "mysql.list_tables":
            tables = data.get("tables", [])
            return f"데이터베이스에 {len(tables)}개의 테이블이 있습니다:\n" + \
                   "\n".join(f"  • {t}" for t in tables)
        
        elif tool_name == "mysql.describe_table":
            table = data.get("table", "")
            columns = data.get("columns", [])
            result = f"테이블 '{table}' 구조:\n"
            for col in columns:
                result += f"  • {col['name']} ({col['type']})"
                if col.get('key') == 'PRI':
                    result += " [PK]"
                result += "\n"
            return result
        
        elif tool_name == "mysql.query":
            rows = data.get("rows", [])
            count = data.get("row_count", 0)
            
            if count == 0:
                return "조회 결과가 없습니다."
            
            result = f"총 {count}건의 데이터:\n\n"
            
            for i, row in enumerate(rows[:5], 1):  # 최대 5개만 표시
                result += f"[{i}] "
                result += ", ".join(f"{k}: {v}" for k, v in row.items())
                result += "\n"
            
            if count > 5:
                result += f"\n... 외 {count - 5}건"
            
            return result
        
        return str(data)
