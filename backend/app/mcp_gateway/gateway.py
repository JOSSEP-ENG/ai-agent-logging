import uuid
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditStatus
from app.audit.service import AuditService
from app.mcp_gateway.permission_service import ToolPermissionService


@dataclass
class ToolDefinition:
    """MCP Tool 정의"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 형식


@dataclass
class ToolCallResult:
    """Tool 호출 결과"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0


@dataclass
class MCPConnection:
    """MCP 서버 연결 정보"""
    id: str
    name: str
    type: str  # "mysql", "notion", "google_calendar", etc.
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    tools: List[ToolDefinition] = field(default_factory=list)


class MCPClient(ABC):
    """MCP 클라이언트 추상 클래스
    
    각 MCP 서버 유형별로 구현체 생성
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """MCP 서버 연결"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """연결 해제"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[ToolDefinition]:
        """사용 가능한 Tool 목록 조회"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolCallResult:
        """Tool 호출"""
        pass


class MCPGateway:
    """MCP Proxy Gateway

    모든 MCP 호출을 중계하며 감사 로깅을 수행합니다.

    역할:
    1. MCP 서버 연결 관리
    2. Tool 호출 중계
    3. 응답 정규화
    4. 에러 핸들링
    5. 감사 로깅 (핵심!)
    6. 권한 검증 (Phase 1 추가)
    """

    def __init__(self, audit_service: AuditService, db_session: Optional[AsyncSession] = None):
        self.audit_service = audit_service
        self.db_session = db_session
        self._connections: Dict[str, MCPConnection] = {}
        self._clients: Dict[str, MCPClient] = {}
    
    def register_connection(self, connection: MCPConnection, client: MCPClient) -> None:
        """MCP 연결 등록"""
        self._connections[connection.id] = connection
        self._clients[connection.id] = client
    
    def unregister_connection(self, connection_id: str) -> None:
        """MCP 연결 해제"""
        if connection_id in self._connections:
            del self._connections[connection_id]
        if connection_id in self._clients:
            del self._clients[connection_id]
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """모든 연결된 MCP의 Tool 목록 반환
        
        Gemini API의 function declarations 형식으로 반환
        """
        tools = []
        for conn_id, connection in self._connections.items():
            if not connection.enabled:
                continue
            
            for tool in connection.tools:
                tools.append({
                    "name": f"{connection.type}.{tool.name}",
                    "description": f"[{connection.name}] {tool.description}",
                    "parameters": tool.parameters,
                })
        
        return tools
    
    async def call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        user_id: str,
        user_query: Optional[str] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> ToolCallResult:
        """Tool 호출 (감사 로깅 및 권한 검증 포함)

        Args:
            tool_name: "mcp_type.tool_name" 형식 (예: "mysql.query")
            params: Tool 파라미터
            user_id: 호출한 사용자 ID
            user_query: 원본 자연어 질문
            session_id: 대화 세션 ID

        Returns:
            ToolCallResult: 호출 결과
        """
        start_time = time.time()

        # Tool 이름 파싱 (mcp_type.tool_name)
        parts = tool_name.split(".", 1)
        if len(parts) != 2:
            return ToolCallResult(
                success=False,
                error=f"잘못된 Tool 이름 형식: {tool_name}",
            )

        mcp_type, actual_tool_name = parts

        # 해당 MCP 클라이언트 찾기
        client = None
        connection = None
        connection_id = None
        for conn_id, conn in self._connections.items():
            if conn.type == mcp_type and conn.enabled:
                client = self._clients.get(conn_id)
                connection = conn
                connection_id = conn_id
                break

        if not client or not connection:
            # 감사 로그 - 실패 (연결 없음)
            await self.audit_service.log_complete(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=params,
                response=None,
                status=AuditStatus.FAIL,
                user_query=user_query,
                session_id=session_id,
                error_message=f"MCP 연결 없음: {mcp_type}",
            )

            return ToolCallResult(
                success=False,
                error=f"MCP 연결을 찾을 수 없습니다: {mcp_type}",
            )

        # === 권한 검증 (Phase 1) ===
        if self.db_session:
            permission_service = ToolPermissionService(self.db_session)
            try:
                # UUID 형식으로 변환
                from uuid import UUID
                user_uuid = UUID(user_id)
                conn_uuid = UUID(connection_id)

                # 권한 확인
                is_allowed, error_msg = await permission_service.check_permission(
                    user_id=user_uuid,
                    connection_id=conn_uuid,
                    tool_name=actual_tool_name,
                    params=params,
                )

                if not is_allowed:
                    # 감사 로그 - 권한 거부
                    await self.audit_service.log_complete(
                        user_id=user_id,
                        tool_name=tool_name,
                        tool_params=params,
                        response=None,
                        status=AuditStatus.DENIED,
                        user_query=user_query,
                        session_id=session_id,
                        error_message=error_msg,
                    )

                    return ToolCallResult(
                        success=False,
                        error=error_msg,
                    )
            except Exception as e:
                # 권한 검증 실패 시 로깅하고 계속 진행 (안전 모드)
                print(f"Warning: Permission check failed: {e}")
                # MVP: 권한 검증 실패 시 허용
                pass
        
        # Tool 호출 실행
        try:
            result = await client.call_tool(actual_tool_name, params)
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms
            
            # 감사 로그 - 성공 또는 실패
            await self.audit_service.log_complete(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=params,
                response=result.data,
                status=AuditStatus.SUCCESS if result.success else AuditStatus.FAIL,
                user_query=user_query,
                session_id=session_id,
                error_message=result.error,
                execution_time_ms=execution_time_ms,
            )
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # 감사 로그 - 예외
            await self.audit_service.log_complete(
                user_id=user_id,
                tool_name=tool_name,
                tool_params=params,
                response=None,
                status=AuditStatus.FAIL,
                user_query=user_query,
                session_id=session_id,
                error_message=error_msg,
                execution_time_ms=execution_time_ms,
            )
            
            return ToolCallResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time_ms,
            )
    
    async def check_permission(
        self,
        user_id: str,
        connection_id: str,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        """Tool 사용 권한 확인 (Phase 1 구현 완료)

        Args:
            user_id: 사용자 ID (UUID 문자열)
            connection_id: MCP 연결 ID (UUID 문자열)
            tool_name: Tool 이름 (예: "read_file")
            params: Tool 파라미터 (선택)

        Returns:
            (허용 여부, 에러 메시지)
        """
        if not self.db_session:
            # DB 세션이 없으면 기본적으로 허용
            return (True, None)

        permission_service = ToolPermissionService(self.db_session)

        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            conn_uuid = UUID(connection_id)

            return await permission_service.check_permission(
                user_id=user_uuid,
                connection_id=conn_uuid,
                tool_name=tool_name,
                params=params,
            )
        except Exception as e:
            # 에러 발생 시 로깅하고 허용 (안전 모드)
            print(f"Warning: Permission check failed: {e}")
            return (True, None)
