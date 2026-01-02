"""대화 관리 서비스 테스트"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.chat.service import ChatService


class TestChatService:
    """ChatService 테스트"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock DB 세션"""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """ChatService 인스턴스"""
        return ChatService(mock_db)
    
    def test_generate_title_short(self, service):
        """짧은 메시지 제목 생성"""
        title = service._generate_title("안녕하세요")
        assert title == "안녕하세요"
    
    def test_generate_title_long(self, service):
        """긴 메시지 제목 생성 (30자 제한)"""
        long_message = "이것은 매우 긴 메시지입니다. 제목으로 사용하기에는 너무 깁니다."
        title = service._generate_title(long_message)
        
        assert len(title) <= 30
        assert title.endswith("...")
    
    def test_generate_title_multiline(self, service):
        """멀티라인 메시지 제목 생성 (첫 줄만)"""
        multiline = "첫 번째 줄\n두 번째 줄\n세 번째 줄"
        title = service._generate_title(multiline)
        
        assert title == "첫 번째 줄"
        assert "\n" not in title
    
    def test_generate_title_empty(self, service):
        """빈 메시지 제목 생성"""
        title = service._generate_title("")
        assert title == "새 대화"
    
    def test_max_history_messages(self, service):
        """최대 히스토리 메시지 수 확인"""
        assert service.MAX_HISTORY_MESSAGES == 20


class TestChatServiceAsync:
    """ChatService 비동기 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """세션 생성 테스트"""
        # Mock 설정
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        service = ChatService(mock_db)
        
        # refresh가 호출될 때 session 객체에 값 설정
        async def mock_refresh(session):
            session.id = uuid4()
            session.created_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # 테스트 실행
        session = await service.create_session(
            user_id="test_user",
            title="테스트 대화",
        )
        
        # 검증
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert session.user_id == "test_user"
        assert session.title == "테스트 대화"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
