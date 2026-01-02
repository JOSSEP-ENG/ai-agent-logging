"""AI Agent 서비스 테스트"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.agent.service import (
    AgentService,
    SimpleAgentService,
    Message,
    AgentResponse,
)
from app.mcp_gateway.gateway import MCPGateway, ToolCallResult


class TestSimpleAgentService:
    """SimpleAgentService 테스트 (Gemini 없이)"""
    
    @pytest.fixture
    def mock_gateway(self):
        """Mock MCP Gateway"""
        gateway = MagicMock(spec=MCPGateway)
        gateway.call_tool = AsyncMock()
        return gateway
    
    @pytest.fixture
    def agent(self, mock_gateway):
        """SimpleAgentService 인스턴스"""
        return SimpleAgentService(mock_gateway)
    
    @pytest.mark.asyncio
    async def test_list_tables_keyword(self, agent, mock_gateway):
        """테이블 목록 키워드 매칭"""
        mock_gateway.call_tool.return_value = ToolCallResult(
            success=True,
            data={"tables": ["customers", "orders", "products"], "count": 3},
        )
        
        response = await agent.process_message(
            user_message="테이블 목록 보여줘",
            user_id="test_user",
        )
        
        assert response.message is not None
        assert "3개의 테이블" in response.message
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "mysql.list_tables"
    
    @pytest.mark.asyncio
    async def test_customer_query_keyword(self, agent, mock_gateway):
        """고객 조회 키워드 매칭"""
        mock_gateway.call_tool.return_value = ToolCallResult(
            success=True,
            data={
                "columns": ["id", "name", "email"],
                "rows": [
                    {"id": 1, "name": "삼성전자", "email": "test@samsung.com"}
                ],
                "row_count": 1,
            },
        )
        
        response = await agent.process_message(
            user_message="고객 목록 보여줘",
            user_id="test_user",
        )
        
        assert response.message is not None
        assert "1건" in response.message
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "mysql.query"
    
    @pytest.mark.asyncio
    async def test_describe_table_keyword(self, agent, mock_gateway):
        """테이블 구조 조회 키워드 매칭"""
        mock_gateway.call_tool.return_value = ToolCallResult(
            success=True,
            data={
                "table": "customers",
                "columns": [
                    {"name": "id", "type": "int", "key": "PRI"},
                    {"name": "name", "type": "varchar(100)", "key": ""},
                ],
            },
        )
        
        response = await agent.process_message(
            user_message="customers 테이블 구조 보여줘",
            user_id="test_user",
        )
        
        assert response.message is not None
        assert "customers" in response.message
        assert "[PK]" in response.message
    
    @pytest.mark.asyncio
    async def test_unknown_message(self, agent, mock_gateway):
        """알 수 없는 메시지"""
        response = await agent.process_message(
            user_message="날씨 알려줘",
            user_id="test_user",
        )
        
        assert "이해하지 못했습니다" in response.message
        assert len(response.tool_calls) == 0
    
    @pytest.mark.asyncio
    async def test_tool_error(self, agent, mock_gateway):
        """Tool 호출 오류"""
        mock_gateway.call_tool.return_value = ToolCallResult(
            success=False,
            error="연결 실패",
        )
        
        response = await agent.process_message(
            user_message="고객 목록 보여줘",
            user_id="test_user",
        )
        
        assert "오류" in response.message
        assert response.error == "연결 실패"


class TestMessage:
    """Message 클래스 테스트"""
    
    def test_message_creation(self):
        """메시지 생성"""
        msg = Message(role="user", content="테스트")
        
        assert msg.role == "user"
        assert msg.content == "테스트"
        assert msg.timestamp is not None
        assert msg.tool_calls == []


class TestAgentResponse:
    """AgentResponse 클래스 테스트"""
    
    def test_response_creation(self):
        """응답 생성"""
        response = AgentResponse(
            message="테스트 응답",
            tool_calls=[{"name": "mysql.query", "args": {}}],
            execution_time_ms=100,
        )
        
        assert response.message == "테스트 응답"
        assert len(response.tool_calls) == 1
        assert response.execution_time_ms == 100
        assert response.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
