"""Tool 권한 테스트 데이터 생성 스크립트

이 스크립트는 Tool 권한 관리 기능을 테스트하기 위한 샘플 데이터를 생성합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.models import get_db, init_db
from app.models.user import User
from app.models.mcp_connection import MCPConnection
from app.models.mcp_tool_permission import MCPToolPermission, PermissionType
from app.models.database import AsyncSessionLocal


async def create_sample_data():
    """샘플 데이터 생성"""

    # 테이블 생성
    print("📋 Creating database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. 사용자 조회 (이미 있어야 함)
        print("\n👥 Loading users...")
        result = await db.execute(select(User))
        users = list(result.scalars().all())

        if not users:
            print("❌ No users found. Please create users first.")
            return

        print(f"✅ Found {len(users)} users")
        for user in users[:3]:  # 처음 3명만 표시
            print(f"   - {user.name} ({user.email}) [{user.role}]")

        # 2. MCP 연결 조회
        print("\n🔌 Loading MCP connections...")
        result = await db.execute(select(MCPConnection))
        connections = list(result.scalars().all())

        if not connections:
            print("⚠️  No MCP connections found. Creating sample connections...")

            # 샘플 연결 생성
            for user in users[:2]:  # 처음 2명의 사용자에게 연결 생성
                # MySQL 연결
                mysql_conn = MCPConnection(
                    user_id=user.id,
                    name=f"{user.name}'s MySQL DB",
                    type="mysql",
                    description="Development MySQL Database",
                    config={
                        "host": "localhost",
                        "port": 3306,
                        "database": "testdb",
                        "read_only": False,
                    },
                    encrypted_credentials="encrypted_dummy_credentials",
                    is_active=True,
                )
                db.add(mysql_conn)

                # Filesystem 연결
                fs_conn = MCPConnection(
                    user_id=user.id,
                    name=f"{user.name}'s File System",
                    type="filesystem",
                    description="File system access for user",
                    config={
                        "base_path": f"/home/{user.name}",
                        "max_file_size_mb": 100,
                    },
                    is_active=True,
                )
                db.add(fs_conn)

            await db.commit()

            # 다시 조회
            result = await db.execute(select(MCPConnection))
            connections = list(result.scalars().all())

        print(f"✅ Found {len(connections)} MCP connections")
        for conn in connections[:3]:
            print(f"   - {conn.name} ({conn.type})")

        # 3. Tool 권한 생성
        print("\n🔐 Creating tool permissions...")

        # 기존 권한 삭제 (재실행 시)
        await db.execute(
            MCPToolPermission.__table__.delete()
        )
        await db.commit()

        permission_count = 0
        admin_user = next((u for u in users if u.role == 'admin'), users[0])

        # 각 사용자별로 권한 설정
        for user in users[:5]:  # 처음 5명의 사용자만
            for conn in connections:
                # MCP 타입별 Tool 목록
                tools_by_type = {
                    "mysql": ["read_query", "write_query", "list_tables", "describe_table"],
                    "filesystem": ["read_file", "write_file", "list_directory", "delete_file"],
                    "notion": ["search_pages", "read_page", "create_page", "update_page"],
                    "google": ["list_events", "create_event", "update_event", "delete_event"],
                }

                tools = tools_by_type.get(conn.type, [])

                for tool_name in tools:
                    # 사용자 역할에 따라 권한 설정
                    if user.role == 'admin':
                        # 관리자: 모든 권한 허용 (명시적 설정 안 함)
                        continue
                    elif user.role == 'auditor':
                        # 감사자: 읽기만 허용, 쓰기/삭제는 차단
                        if any(keyword in tool_name for keyword in ['write', 'delete', 'create', 'update']):
                            permission_type = PermissionType.BLOCKED
                        else:
                            permission_type = PermissionType.ALLOWED
                    else:  # user
                        # 일반 사용자: 일부는 허용, 일부는 차단
                        if tool_name in ['delete_file', 'write_query']:
                            permission_type = PermissionType.BLOCKED
                        elif tool_name in ['read_file', 'read_query', 'list_tables']:
                            permission_type = PermissionType.ALLOWED
                        else:
                            # 나머지는 설정하지 않음 (기본 허용)
                            continue

                    permission = MCPToolPermission(
                        user_id=user.id,
                        connection_id=conn.id,
                        tool_name=tool_name,
                        permission_type=permission_type,
                        created_by=admin_user.id,
                    )
                    db.add(permission)
                    permission_count += 1

        await db.commit()
        print(f"✅ Created {permission_count} tool permissions")

        # 4. 생성된 권한 요약 표시
        print("\n📊 Permission Summary:")
        result = await db.execute(
            select(MCPToolPermission)
            .order_by(MCPToolPermission.user_id, MCPToolPermission.connection_id)
        )
        permissions = list(result.scalars().all())

        # 사용자별로 그룹화
        by_user = {}
        for perm in permissions:
            user = next((u for u in users if u.id == perm.user_id), None)
            if not user:
                continue

            user_key = f"{user.name} ({user.role})"
            if user_key not in by_user:
                by_user[user_key] = {"allowed": 0, "blocked": 0}

            if perm.permission_type == PermissionType.ALLOWED:
                by_user[user_key]["allowed"] += 1
            else:
                by_user[user_key]["blocked"] += 1

        for user_key, counts in by_user.items():
            print(f"   {user_key}: {counts['allowed']} allowed, {counts['blocked']} blocked")

        print("\n✨ Sample data creation completed!")
        print("\n💡 Next steps:")
        print("   1. Start the backend server: python -m uvicorn app.main:app --reload")
        print("   2. Login as admin and go to Settings > Permissions tab")
        print("   3. Select a user and MCP connection to view/modify tool permissions")


if __name__ == "__main__":
    print("🚀 Tool Permissions Sample Data Generator\n")
    asyncio.run(create_sample_data())
