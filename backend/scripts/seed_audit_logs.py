"""감사 로그 샘플 데이터 생성 스크립트

다양한 상황의 감사 로그를 생성하여 UI 테스트 및 분석 기능을 검증합니다.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.models import get_db, init_db
from app.models.user import User
from app.models.audit import AuditLog, AuditStatus
from app.models.chat import ChatSession
from app.models.database import AsyncSessionLocal


# 다양한 Tool 호출 시나리오
TOOL_SCENARIOS = [
    # 파일 시스템 작업
    {
        "tool_name": "filesystem.read_file",
        "params": {"path": "/home/user/documents/report.pdf"},
        "response": {"content": "파일 내용...", "size_bytes": 1024},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 45,
    },
    {
        "tool_name": "filesystem.write_file",
        "params": {"path": "/home/user/output.txt", "content": "Hello World"},
        "response": {"success": True, "bytes_written": 11},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 32,
    },
    {
        "tool_name": "filesystem.delete_file",
        "params": {"path": "/tmp/cache.dat"},
        "response": None,
        "status": AuditStatus.DENIED,
        "error": "Tool 'delete_file' 사용이 차단되었습니다",
        "execution_time_ms": 5,
    },
    {
        "tool_name": "filesystem.list_directory",
        "params": {"path": "/home/user"},
        "response": {"files": ["doc1.txt", "doc2.pdf", "image.png"], "count": 3},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 28,
    },

    # 데이터베이스 작업
    {
        "tool_name": "mysql.read_query",
        "params": {"query": "SELECT * FROM users LIMIT 10"},
        "response": {"rows": 10, "columns": ["id", "name", "email"]},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 156,
    },
    {
        "tool_name": "mysql.write_query",
        "params": {"query": "UPDATE users SET status='active' WHERE id=5"},
        "response": None,
        "status": AuditStatus.DENIED,
        "error": "Tool 'write_query' 사용이 차단되었습니다",
        "execution_time_ms": 8,
    },
    {
        "tool_name": "mysql.list_tables",
        "params": {},
        "response": {"tables": ["users", "sessions", "audit_logs"]},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 42,
    },
    {
        "tool_name": "mysql.describe_table",
        "params": {"table": "users"},
        "response": {"columns": [{"name": "id", "type": "UUID"}, {"name": "email", "type": "VARCHAR"}]},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 38,
    },

    # Notion 작업
    {
        "tool_name": "notion.search_pages",
        "params": {"query": "프로젝트 계획"},
        "response": {"results": [{"id": "page1", "title": "2024 프로젝트 계획"}], "count": 1},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 234,
    },
    {
        "tool_name": "notion.read_page",
        "params": {"page_id": "abc123"},
        "response": {"title": "회의록", "content": "..."},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 189,
    },
    {
        "tool_name": "notion.create_page",
        "params": {"title": "새 페이지", "content": "내용"},
        "response": {"id": "new_page_123", "url": "https://notion.so/..."},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 567,
    },

    # Google Calendar 작업
    {
        "tool_name": "google.list_events",
        "params": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
        "response": {"events": [{"id": "event1", "title": "팀 미팅"}], "count": 1},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 345,
    },
    {
        "tool_name": "google.create_event",
        "params": {"title": "새 미팅", "start": "2026-01-15T10:00:00"},
        "response": {"id": "event_new", "url": "https://calendar.google.com/..."},
        "status": AuditStatus.SUCCESS,
        "execution_time_ms": 423,
    },

    # 실패 케이스
    {
        "tool_name": "filesystem.read_file",
        "params": {"path": "/root/secret.txt"},
        "response": None,
        "status": AuditStatus.FAIL,
        "error": "Permission denied: /root/secret.txt",
        "execution_time_ms": 12,
    },
    {
        "tool_name": "mysql.read_query",
        "params": {"query": "SELECT * FROM non_existent_table"},
        "response": None,
        "status": AuditStatus.FAIL,
        "error": "Table 'non_existent_table' doesn't exist",
        "execution_time_ms": 23,
    },
    {
        "tool_name": "notion.read_page",
        "params": {"page_id": "invalid_id"},
        "response": None,
        "status": AuditStatus.FAIL,
        "error": "Page not found: invalid_id",
        "execution_time_ms": 178,
    },
]

# 인증 및 권한 이벤트
AUTH_SCENARIOS = [
    {
        "tool_name": "login",
        "params": {"email": "user@example.com"},
        "response": {"success": True},
        "status": AuditStatus.SUCCESS,
    },
    {
        "tool_name": "login",
        "params": {"email": "hacker@bad.com"},
        "response": {"success": False},
        "status": AuditStatus.FAIL,
        "error": "Invalid credentials",
    },
    {
        "tool_name": "logout",
        "params": {},
        "response": {"success": True},
        "status": AuditStatus.SUCCESS,
    },
    {
        "tool_name": "change_user_role",
        "params": {
            "target_user_id": "user_123",
            "target_user_email": "john@company.com",
            "old_role": "user",
            "new_role": "admin",
        },
        "response": {"success": True},
        "status": AuditStatus.SUCCESS,
    },
    {
        "tool_name": "enable_mcp_connection",
        "params": {
            "connection_id": "mcp_123",
            "connection_name": "MySQL Production",
        },
        "response": {"enabled": True},
        "status": AuditStatus.SUCCESS,
    },
    {
        "tool_name": "disable_mcp_connection",
        "params": {
            "connection_id": "mcp_456",
            "connection_name": "File System",
        },
        "response": {"enabled": False},
        "status": AuditStatus.SUCCESS,
    },
]

# 사용자 질의 예시
USER_QUERIES = [
    "데이터베이스에서 사용자 목록을 조회해줘",
    "파일 시스템에서 report.pdf를 읽어줘",
    "Notion에서 프로젝트 계획 페이지를 찾아줘",
    "오늘 일정을 보여줘",
    "/home/user 디렉토리의 파일 목록을 보여줘",
    "users 테이블의 구조를 알려줘",
    "새 회의 일정을 생성해줘",
    "캐시 파일을 삭제해줘",
    "데이터베이스를 업데이트해줘",
    None,  # 직접 Tool 호출
]


async def create_audit_logs():
    """감사 로그 샘플 데이터 생성"""

    print("📋 Creating database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. 사용자 조회
        print("\n👥 Loading users...")
        result = await db.execute(select(User))
        users = list(result.scalars().all())

        if not users:
            print("❌ No users found. Please create users first.")
            return

        print(f"✅ Found {len(users)} users")

        # 2. 세션 조회
        result = await db.execute(select(ChatSession))
        sessions = list(result.scalars().all())

        print(f"✅ Found {len(sessions)} chat sessions")

        # 3. 기존 감사 로그 삭제
        print("\n🗑️  Clearing existing audit logs...")
        await db.execute(AuditLog.__table__.delete())
        await db.commit()

        # 4. 감사 로그 생성
        print("\n📝 Creating diverse audit logs...")

        logs_created = 0

        # 과거 30일 동안의 로그 생성
        now = datetime.utcnow()

        for day_offset in range(30):
            # 각 날짜마다 여러 로그 생성
            date = now - timedelta(days=day_offset)

            # 하루에 5-20개의 로그
            daily_log_count = random.randint(5, 20)

            for _ in range(daily_log_count):
                # 랜덤 시간 (업무 시간 위주)
                hour = random.choices(
                    range(24),
                    weights=[1, 1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 10, 8, 10, 10, 8, 5, 3, 2, 1, 1, 1, 1, 1]
                )[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)

                timestamp = date.replace(hour=hour, minute=minute, second=second)

                # 랜덤 사용자
                user = random.choice(users)

                # 80% Tool 호출, 20% 인증/권한 이벤트
                if random.random() < 0.8:
                    scenario = random.choice(TOOL_SCENARIOS)
                    user_query = random.choice(USER_QUERIES)
                    session = random.choice(sessions) if sessions and random.random() < 0.7 else None
                else:
                    scenario = random.choice(AUTH_SCENARIOS)
                    user_query = None
                    session = None

                log = AuditLog(
                    user_id=str(user.id),
                    session_id=session.id if session else None,
                    user_query=user_query,
                    tool_name=scenario["tool_name"],
                    tool_params=scenario["params"],
                    response=scenario.get("response"),
                    status=scenario["status"],
                    error_message=scenario.get("error"),
                    execution_time_ms=str(scenario.get("execution_time_ms", random.randint(10, 500))),
                    timestamp=timestamp,
                )

                db.add(log)
                logs_created += 1

        await db.commit()
        print(f"✅ Created {logs_created} audit logs")

        # 5. 통계 출력
        print("\n📊 Audit Log Statistics:")

        result = await db.execute(select(AuditLog))
        all_logs = list(result.scalars().all())

        # 상태별 통계
        status_counts = {}
        for log in all_logs:
            status = log.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\n  상태별 분포:")
        for status, count in sorted(status_counts.items()):
            percentage = (count / len(all_logs)) * 100
            print(f"    - {status}: {count} ({percentage:.1f}%)")

        # Tool별 통계
        tool_counts = {}
        for log in all_logs:
            tool = log.tool_name
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        print("\n  상위 10개 Tool:")
        top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for tool, count in top_tools:
            print(f"    - {tool}: {count}")

        # 사용자별 통계
        user_counts = {}
        for log in all_logs:
            user_id = log.user_id
            user = next((u for u in users if str(u.id) == user_id), None)
            if user:
                user_name = f"{user.name} ({user.role})"
                user_counts[user_name] = user_counts.get(user_name, 0) + 1

        print("\n  사용자별 활동:")
        for user_name, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {user_name}: {count}")

        # 날짜별 통계 (최근 7일)
        daily_counts = {}
        for log in all_logs:
            date_str = log.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

        print("\n  최근 7일 활동:")
        recent_dates = sorted(daily_counts.keys(), reverse=True)[:7]
        for date_str in recent_dates:
            count = daily_counts[date_str]
            print(f"    - {date_str}: {count}")

        print("\n✨ Audit log sample data creation completed!")
        print("\n💡 Next steps:")
        print("   1. Start the backend server: python -m uvicorn app.main:app --reload")
        print("   2. Login and go to Audit Logs page")
        print("   3. Test filtering by status, tool name, date range, etc.")
        print("   4. View detailed log information")


if __name__ == "__main__":
    print("🚀 Audit Logs Sample Data Generator\n")
    asyncio.run(create_audit_logs())
