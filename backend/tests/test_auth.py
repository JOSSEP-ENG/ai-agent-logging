"""인증 서비스 테스트"""
import pytest
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import UserRole, User


class TestPasswordUtils:
    """비밀번호 유틸리티 테스트"""
    
    def test_hash_password(self):
        """비밀번호 해싱"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """올바른 비밀번호 검증"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """잘못된 비밀번호 검증"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password("wrong_password", hashed) is False
    
    def test_different_hashes_same_password(self):
        """같은 비밀번호도 다른 해시 생성 (salt)"""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        # 하지만 둘 다 검증은 통과
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTUtils:
    """JWT 유틸리티 테스트"""
    
    def test_create_access_token(self):
        """액세스 토큰 생성"""
        data = {"sub": "user_123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert len(token) > 0
    
    def test_decode_access_token(self):
        """액세스 토큰 디코딩"""
        data = {"sub": "user_123", "email": "test@example.com"}
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user_123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_decode_invalid_token(self):
        """잘못된 토큰 디코딩"""
        payload = decode_access_token("invalid_token")
        
        assert payload is None
    
    def test_decode_tampered_token(self):
        """변조된 토큰 디코딩"""
        data = {"sub": "user_123"}
        token = create_access_token(data)
        
        # 토큰 변조
        tampered = token[:-5] + "xxxxx"
        payload = decode_access_token(tampered)
        
        assert payload is None


class TestUserRole:
    """UserRole 테스트"""
    
    def test_role_values(self):
        """역할 값 확인"""
        assert UserRole.USER.value == "user"
        assert UserRole.AUDITOR.value == "auditor"
        assert UserRole.ADMIN.value == "admin"
    
    def test_user_has_permission_same_role(self):
        """같은 역할 권한 확인"""
        user = User(
            email="test@test.com",
            password_hash="hash",
            name="Test",
            role=UserRole.USER,
        )
        
        assert user.has_permission(UserRole.USER) is True
    
    def test_user_has_permission_higher_role(self):
        """상위 역할 권한 확인"""
        admin = User(
            email="admin@test.com",
            password_hash="hash",
            name="Admin",
            role=UserRole.ADMIN,
        )
        
        # Admin은 모든 권한 보유
        assert admin.has_permission(UserRole.USER) is True
        assert admin.has_permission(UserRole.AUDITOR) is True
        assert admin.has_permission(UserRole.ADMIN) is True
    
    def test_user_has_permission_lower_role(self):
        """하위 역할 권한 미보유"""
        user = User(
            email="test@test.com",
            password_hash="hash",
            name="Test",
            role=UserRole.USER,
        )
        
        # User는 상위 권한 없음
        assert user.has_permission(UserRole.AUDITOR) is False
        assert user.has_permission(UserRole.ADMIN) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
