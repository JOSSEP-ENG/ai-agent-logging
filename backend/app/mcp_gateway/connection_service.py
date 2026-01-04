"""MCP 연결 관리 서비스

사용자별 MCP 연결 정보의 CRUD 작업을 처리합니다.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.mcp_connection import MCPConnection
from app.mcp_gateway.encryption import EncryptionService


class MCPConnectionService:
    """MCP 연결 정보 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = EncryptionService()

    async def create_connection(
        self,
        user_id: UUID,
        name: str,
        type: str,
        config: dict,
        credentials: dict,
        description: Optional[str] = None,
    ) -> MCPConnection:
        """MCP 연결 생성 (credentials 암호화)

        Args:
            user_id: 사용자 ID
            name: 연결 이름 (예: "Production MySQL")
            type: 연결 타입 (예: "mysql", "notion")
            config: 설정 정보 (예: {"host": "localhost", "port": 3306})
            credentials: 인증 정보 (예: {"username": "root", "password": "1234"})
            description: 연결 설명 (선택)

        Returns:
            생성된 MCPConnection 객체
        """
        # credentials 암호화
        encrypted_creds = self.encryption.encrypt(credentials) if credentials else None

        connection = MCPConnection(
            user_id=user_id,
            name=name,
            type=type,
            description=description,
            config=config,
            encrypted_credentials=encrypted_creds,
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def get_user_connections(
        self,
        user_id: UUID,
        active_only: bool = True,
    ) -> List[MCPConnection]:
        """사용자의 모든 MCP 연결 조회

        Args:
            user_id: 사용자 ID
            active_only: True일 경우 활성화된 연결만 조회

        Returns:
            MCPConnection 리스트
        """
        query = select(MCPConnection).where(MCPConnection.user_id == user_id)

        if active_only:
            query = query.where(MCPConnection.is_active == True)

        query = query.order_by(MCPConnection.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
    ) -> Optional[MCPConnection]:
        """특정 MCP 연결 조회 (사용자 격리)

        Args:
            connection_id: 연결 ID
            user_id: 사용자 ID (접근 권한 확인용)

        Returns:
            MCPConnection 또는 None
        """
        query = select(MCPConnection).where(
            and_(
                MCPConnection.id == connection_id,
                MCPConnection.user_id == user_id,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
        credentials: Optional[dict] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[MCPConnection]:
        """MCP 연결 정보 업데이트

        Args:
            connection_id: 연결 ID
            user_id: 사용자 ID
            name: 새 연결 이름 (선택)
            description: 새 설명 (선택)
            config: 새 설정 (선택)
            credentials: 새 인증정보 (선택, 암호화됨)
            is_active: 활성화 상태 (선택)

        Returns:
            업데이트된 MCPConnection 또는 None
        """
        connection = await self.get_connection(connection_id, user_id)
        if not connection:
            return None

        if name is not None:
            connection.name = name
        if description is not None:
            connection.description = description
        if config is not None:
            connection.config = config
        if credentials is not None:
            connection.encrypted_credentials = self.encryption.encrypt(credentials)
        if is_active is not None:
            connection.is_active = is_active

        connection.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    async def delete_connection(
        self,
        connection_id: UUID,
        user_id: UUID,
    ) -> bool:
        """MCP 연결 삭제

        Args:
            connection_id: 연결 ID
            user_id: 사용자 ID

        Returns:
            삭제 성공 여부
        """
        connection = await self.get_connection(connection_id, user_id)
        if not connection:
            return False

        await self.db.delete(connection)
        await self.db.commit()
        return True

    async def update_test_status(
        self,
        connection_id: UUID,
        user_id: UUID,
        status: str,
        error: Optional[str] = None,
    ) -> Optional[MCPConnection]:
        """연결 테스트 결과 업데이트

        Args:
            connection_id: 연결 ID
            user_id: 사용자 ID
            status: 테스트 상태 ("success" 또는 "failed")
            error: 에러 메시지 (실패 시)

        Returns:
            업데이트된 MCPConnection 또는 None
        """
        connection = await self.get_connection(connection_id, user_id)
        if not connection:
            return None

        connection.last_tested_at = datetime.utcnow()
        connection.last_test_status = status
        connection.last_test_error = error

        await self.db.commit()
        await self.db.refresh(connection)
        return connection

    def get_decrypted_credentials(self, connection: MCPConnection) -> dict:
        """암호화된 credentials 복호화

        Args:
            connection: MCPConnection 객체

        Returns:
            복호화된 인증정보 딕셔너리
        """
        if not connection.encrypted_credentials:
            return {}
        return self.encryption.decrypt(connection.encrypted_credentials)
