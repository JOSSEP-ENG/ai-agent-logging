"""MCP Tool 권한 관리 서비스

사용자별 Tool 권한의 CRUD 작업을 처리합니다.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.models.mcp_tool_permission import MCPToolPermission, PermissionType
from app.models.mcp_connection import MCPConnection


class ToolPermissionService:
    """Tool 권한 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_permissions(
        self,
        user_id: UUID,
        connection_id: Optional[UUID] = None,
    ) -> List[MCPToolPermission]:
        """사용자의 Tool 권한 조회

        Args:
            user_id: 사용자 ID
            connection_id: MCP 연결 ID (선택, 특정 연결만 조회)

        Returns:
            MCPToolPermission 리스트
        """
        query = select(MCPToolPermission).where(MCPToolPermission.user_id == user_id)

        if connection_id:
            query = query.where(MCPToolPermission.connection_id == connection_id)

        query = query.order_by(
            MCPToolPermission.connection_id,
            MCPToolPermission.tool_name,
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_permission(
        self,
        user_id: UUID,
        connection_id: UUID,
        tool_name: str,
    ) -> Optional[MCPToolPermission]:
        """특정 Tool 권한 조회

        Args:
            user_id: 사용자 ID
            connection_id: MCP 연결 ID
            tool_name: Tool 이름

        Returns:
            MCPToolPermission 또는 None
        """
        query = select(MCPToolPermission).where(
            and_(
                MCPToolPermission.user_id == user_id,
                MCPToolPermission.connection_id == connection_id,
                MCPToolPermission.tool_name == tool_name,
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def set_permission(
        self,
        user_id: UUID,
        connection_id: UUID,
        tool_name: str,
        permission_type: PermissionType,
        created_by: UUID,
        param_constraints: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        time_restrictions: Optional[Dict[str, Any]] = None,
        rate_limit: Optional[Dict[str, Any]] = None,
    ) -> MCPToolPermission:
        """Tool 권한 설정 (생성 또는 업데이트)

        Args:
            user_id: 사용자 ID
            connection_id: MCP 연결 ID
            tool_name: Tool 이름
            permission_type: 권한 유형 (allowed/blocked/approval_required)
            created_by: 권한을 설정한 관리자 ID
            param_constraints: 파라미터 제약 조건 (선택)
            expires_at: 권한 만료 시간 (선택)
            time_restrictions: 시간 제약 (선택)
            rate_limit: 호출 제한 (선택)

        Returns:
            생성/업데이트된 MCPToolPermission
        """
        # 기존 권한 조회
        existing = await self.get_permission(user_id, connection_id, tool_name)

        if existing:
            # 업데이트
            existing.permission_type = permission_type
            existing.param_constraints = param_constraints
            existing.expires_at = expires_at
            existing.time_restrictions = time_restrictions
            existing.rate_limit = rate_limit
            existing.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # 새로 생성
            permission = MCPToolPermission(
                user_id=user_id,
                connection_id=connection_id,
                tool_name=tool_name,
                permission_type=permission_type,
                created_by=created_by,
                param_constraints=param_constraints,
                expires_at=expires_at,
                time_restrictions=time_restrictions,
                rate_limit=rate_limit,
            )

            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)
            return permission

    async def delete_permission(
        self,
        permission_id: UUID,
    ) -> bool:
        """Tool 권한 삭제

        Args:
            permission_id: 권한 ID

        Returns:
            삭제 성공 여부
        """
        query = delete(MCPToolPermission).where(MCPToolPermission.id == permission_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    async def check_permission(
        self,
        user_id: UUID,
        connection_id: UUID,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        """Tool 사용 권한 검증

        Args:
            user_id: 사용자 ID
            connection_id: MCP 연결 ID
            tool_name: Tool 이름
            params: Tool 파라미터 (파라미터 제약 검증용)

        Returns:
            (허용 여부, 에러 메시지)
        """
        # 1. 권한 조회
        permission = await self.get_permission(user_id, connection_id, tool_name)

        # 권한이 설정되지 않은 경우 - 기본적으로 허용 (MVP)
        if not permission:
            return (True, None)

        # 2. 차단된 경우
        if permission.permission_type == PermissionType.BLOCKED:
            return (False, f"Tool '{tool_name}' 사용이 차단되었습니다")

        # 3. 승인 필요 (향후 구현)
        if permission.permission_type == PermissionType.APPROVAL_REQUIRED:
            return (False, f"Tool '{tool_name}' 사용에 관리자 승인이 필요합니다")

        # 4. 시간 만료 확인
        if permission.is_expired():
            return (False, f"Tool '{tool_name}' 권한이 만료되었습니다")

        # 5. 시간 제약 확인
        if not permission.is_time_allowed():
            return (False, f"Tool '{tool_name}'는 현재 시간에 사용할 수 없습니다")

        # 6. 파라미터 제약 확인 (Phase 2 - 향후 구현)
        if permission.param_constraints and params:
            # TODO: 파라미터 검증 로직
            pass

        # 7. Rate Limiting (Phase 4 - 향후 구현)
        if permission.rate_limit:
            # TODO: Rate limit 검증 로직
            pass

        return (True, None)

    async def get_connection_tools(
        self,
        connection_id: UUID,
    ) -> List[str]:
        """특정 MCP 연결의 Tool 목록 조회

        Args:
            connection_id: MCP 연결 ID

        Returns:
            Tool 이름 리스트
        """
        # TODO: 실제로는 MCP Gateway에서 연결된 서버의 Tool 목록을 가져와야 함
        # 현재는 더미 데이터 반환
        query = select(MCPConnection).where(MCPConnection.id == connection_id)
        result = await self.db.execute(query)
        connection = result.scalar_one_or_none()

        if not connection:
            return []

        # MCP 타입별 기본 Tool 목록 (향후 동적으로 가져오기)
        default_tools = {
            "mysql": ["read_query", "write_query", "list_tables", "describe_table"],
            "filesystem": ["read_file", "write_file", "list_directory", "delete_file"],
            "notion": ["search_pages", "read_page", "create_page", "update_page"],
            "google": ["list_events", "create_event", "update_event", "delete_event"],
        }

        return default_tools.get(connection.type, [])

    async def bulk_set_permissions(
        self,
        user_id: UUID,
        connection_id: UUID,
        tool_permissions: Dict[str, PermissionType],
        created_by: UUID,
    ) -> List[MCPToolPermission]:
        """여러 Tool의 권한을 일괄 설정

        Args:
            user_id: 사용자 ID
            connection_id: MCP 연결 ID
            tool_permissions: {tool_name: permission_type} 딕셔너리
            created_by: 권한을 설정한 관리자 ID

        Returns:
            생성/업데이트된 MCPToolPermission 리스트
        """
        results = []
        for tool_name, permission_type in tool_permissions.items():
            permission = await self.set_permission(
                user_id=user_id,
                connection_id=connection_id,
                tool_name=tool_name,
                permission_type=permission_type,
                created_by=created_by,
            )
            results.append(permission)

        return results
