"""사용자별 MCP Gateway 관리자

각 사용자마다 독립적인 MCP Gateway 인스턴스를 관리합니다.
"""
from typing import Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_gateway.gateway import MCPGateway, MCPConnection as GatewayConnection
from app.mcp_gateway.connection_service import MCPConnectionService
from app.mcp_gateway.mysql_client import MySQLMCPClient
from app.audit.service import AuditService


class UserGatewayManager:
    """사용자별 MCP Gateway 인스턴스 관리자

    역할:
    1. 사용자 ID → Gateway 인스턴스 매핑 (캐싱)
    2. DB에서 사용자별 MCP 연결 로드
    3. 각 연결에 대한 MCPClient 생성 및 Gateway 등록
    4. 연결 변경 시 Gateway 재로드
    """

    def __init__(self, audit_service: AuditService):
        self._user_gateways: Dict[UUID, MCPGateway] = {}
        self.audit_service = audit_service

    async def get_user_gateway(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> MCPGateway:
        """사용자 전용 Gateway 가져오기 (없으면 생성)

        Args:
            user_id: 사용자 ID
            db: DB 세션

        Returns:
            MCPGateway: 사용자 전용 Gateway 인스턴스
        """
        # 캐싱: 이미 로드된 Gateway는 재사용
        if user_id not in self._user_gateways:
            gateway = MCPGateway(self.audit_service)
            await self._load_user_connections(gateway, user_id, db)
            self._user_gateways[user_id] = gateway

        return self._user_gateways[user_id]

    async def reload_user_gateway(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """사용자 Gateway 재로드 (연결 추가/삭제 시 호출)

        Args:
            user_id: 사용자 ID
            db: DB 세션
        """
        # 기존 Gateway 제거
        if user_id in self._user_gateways:
            # 기존 연결 정리
            old_gateway = self._user_gateways[user_id]
            # TODO: 연결된 클라이언트들의 disconnect() 호출 필요
            del self._user_gateways[user_id]

        # 새 Gateway 로드
        await self.get_user_gateway(user_id, db)

    async def _load_user_connections(
        self,
        gateway: MCPGateway,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """DB에서 사용자의 MCP 연결을 로드하여 Gateway에 등록

        Args:
            gateway: MCPGateway 인스턴스
            user_id: 사용자 ID
            db: DB 세션
        """
        service = MCPConnectionService(db)
        connections = await service.get_user_connections(user_id, active_only=True)

        for conn in connections:
            try:
                if conn.type == "mysql":
                    await self._register_mysql_connection(gateway, service, conn)
                # TODO: Phase 3에서 Notion, Google 등 추가
                # elif conn.type == "notion":
                #     await self._register_notion_connection(gateway, service, conn)

            except Exception as e:
                print(f"⚠️ 연결 로드 실패 [{conn.name}]: {e}")
                # 연결 실패해도 계속 진행 (다른 연결은 사용 가능)
                continue

    async def _register_mysql_connection(
        self,
        gateway: MCPGateway,
        service: MCPConnectionService,
        conn,
    ) -> None:
        """MySQL 연결을 Gateway에 등록

        Args:
            gateway: MCPGateway 인스턴스
            service: MCPConnectionService 인스턴스
            conn: MCPConnection 모델 인스턴스
        """
        # credentials 복호화
        credentials = service.get_decrypted_credentials(conn)

        # MySQL 클라이언트 생성
        client = MySQLMCPClient(
            host=conn.config.get("host", "localhost"),
            port=conn.config.get("port", 3306),
            user=credentials.get("username", ""),
            password=credentials.get("password", ""),
            database=conn.config.get("database", ""),
            read_only=conn.config.get("read_only", True),
        )

        # 연결 시도
        connected = await client.connect()
        if not connected:
            raise Exception(f"MySQL 연결 실패: {conn.name}")

        # Tool 목록 조회
        tools = await client.list_tools()

        # Gateway 연결 정보 생성
        gateway_conn = GatewayConnection(
            id=str(conn.id),
            name=conn.name,
            type=conn.type,
            config=conn.config,
            enabled=conn.is_active,
            tools=tools,
        )

        # Gateway에 등록
        gateway.register_connection(gateway_conn, client)
        print(f"✅ MySQL 연결 로드: {conn.name} ({len(tools)} tools)")
