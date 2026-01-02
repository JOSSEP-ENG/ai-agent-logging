import asyncio
from typing import Any, Dict, List, Optional
import json

from app.mcp_gateway.gateway import MCPClient, ToolDefinition, ToolCallResult


class MySQLMCPClient(MCPClient):
    """MySQL MCP 클라이언트
    
    MySQL 데이터베이스와 MCP 프로토콜을 통해 통신합니다.
    실제로는 @benborla29/mcp-server-mysql 서버와 통신하지만,
    MVP에서는 직접 MySQL 연결로 구현합니다.
    
    지원 Tool:
    - query: SQL 쿼리 실행 (SELECT만)
    - list_tables: 테이블 목록 조회
    - describe_table: 테이블 구조 조회
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        read_only: bool = True,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.read_only = read_only
        self._connection = None
        self._pool = None
    
    async def connect(self) -> bool:
        """MySQL 연결"""
        try:
            import aiomysql
            
            self._pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                autocommit=True,
                minsize=1,
                maxsize=5,
            )
            return True
        except Exception as e:
            print(f"MySQL 연결 실패: {e}")
            return False
    
    async def disconnect(self) -> None:
        """연결 해제"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
    
    async def list_tools(self) -> List[ToolDefinition]:
        """사용 가능한 Tool 목록"""
        return [
            ToolDefinition(
                name="query",
                description="SQL SELECT 쿼리를 실행합니다. 읽기 전용입니다.",
                parameters={
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "실행할 SELECT SQL 쿼리",
                        },
                        "params": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "SQL 파라미터 (선택)",
                        },
                    },
                    "required": ["sql"],
                },
            ),
            ToolDefinition(
                name="list_tables",
                description="데이터베이스의 모든 테이블 목록을 조회합니다.",
                parameters={
                    "type": "object",
                    "properties": {},
                },
            ),
            ToolDefinition(
                name="describe_table",
                description="테이블의 구조(컬럼, 타입)를 조회합니다.",
                parameters={
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "테이블 이름",
                        },
                    },
                    "required": ["table"],
                },
            ),
        ]
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolCallResult:
        """Tool 호출"""
        if not self._pool:
            return ToolCallResult(
                success=False,
                error="MySQL 연결이 없습니다. connect()를 먼저 호출하세요.",
            )
        
        try:
            if tool_name == "query":
                return await self._execute_query(params)
            elif tool_name == "list_tables":
                return await self._list_tables()
            elif tool_name == "describe_table":
                return await self._describe_table(params)
            else:
                return ToolCallResult(
                    success=False,
                    error=f"알 수 없는 Tool: {tool_name}",
                )
        except Exception as e:
            return ToolCallResult(
                success=False,
                error=str(e),
            )
    
    async def _execute_query(self, params: Dict[str, Any]) -> ToolCallResult:
        """SQL 쿼리 실행"""
        sql = params.get("sql", "")
        query_params = params.get("params", [])
        
        # 읽기 전용 검증
        if self.read_only:
            sql_upper = sql.upper().strip()
            if not sql_upper.startswith("SELECT"):
                return ToolCallResult(
                    success=False,
                    error="읽기 전용 모드입니다. SELECT 쿼리만 허용됩니다.",
                )
        
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql, query_params or None)
                
                # 컬럼 이름 가져오기
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 결과 가져오기
                rows = await cursor.fetchall()
                
                # 딕셔너리 형태로 변환
                result = [
                    dict(zip(columns, row))
                    for row in rows
                ]
                
                return ToolCallResult(
                    success=True,
                    data={
                        "columns": columns,
                        "rows": result,
                        "row_count": len(result),
                    },
                )
    
    async def _list_tables(self) -> ToolCallResult:
        """테이블 목록 조회"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                rows = await cursor.fetchall()
                
                tables = [row[0] for row in rows]
                
                return ToolCallResult(
                    success=True,
                    data={
                        "tables": tables,
                        "count": len(tables),
                    },
                )
    
    async def _describe_table(self, params: Dict[str, Any]) -> ToolCallResult:
        """테이블 구조 조회"""
        table = params.get("table", "")
        
        if not table:
            return ToolCallResult(
                success=False,
                error="테이블 이름이 필요합니다.",
            )
        
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 테이블 존재 확인
                await cursor.execute("SHOW TABLES LIKE %s", (table,))
                if not await cursor.fetchone():
                    return ToolCallResult(
                        success=False,
                        error=f"테이블을 찾을 수 없습니다: {table}",
                    )
                
                # 테이블 구조 조회
                await cursor.execute(f"DESCRIBE `{table}`")
                rows = await cursor.fetchall()
                
                columns = []
                for row in rows:
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "null": row[2],
                        "key": row[3],
                        "default": row[4],
                        "extra": row[5],
                    })
                
                return ToolCallResult(
                    success=True,
                    data={
                        "table": table,
                        "columns": columns,
                    },
                )
