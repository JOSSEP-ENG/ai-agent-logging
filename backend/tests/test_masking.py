"""민감정보 마스킹 테스트"""
import pytest
from app.audit.masking import DataMasker


class TestDataMasker:
    """DataMasker 테스트"""
    
    def test_mask_ssn(self):
        """주민등록번호 마스킹"""
        # 하이픈 있는 경우
        assert DataMasker.mask_string("주민번호: 900101-1234567") == "주민번호: ******-*******"
        # 하이픈 없는 경우
        assert DataMasker.mask_string("주민번호: 9001011234567") == "주민번호: ******-*******"
    
    def test_mask_card_number(self):
        """카드번호 마스킹"""
        # 하이픈 있는 경우
        result = DataMasker.mask_string("카드: 1234-5678-9012-3456")
        assert result == "카드: ****-****-****-3456"
        
        # 하이픈 없는 경우
        result = DataMasker.mask_string("카드: 1234567890123456")
        assert result == "카드: ****-****-****-3456"
    
    def test_mask_email(self):
        """이메일 마스킹"""
        result = DataMasker.mask_string("이메일: kim@company.com")
        assert "k" in result
        assert "**@company.com" in result
    
    def test_mask_phone(self):
        """전화번호 마스킹"""
        # 하이픈 있는 경우
        result = DataMasker.mask_string("전화: 010-1234-5678")
        assert result == "전화: 010-****-5678"
        
        # 하이픈 없는 경우
        result = DataMasker.mask_string("전화: 01012345678")
        assert result == "전화: 010-****-5678"
    
    def test_mask_account(self):
        """계좌번호 마스킹"""
        result = DataMasker.mask_string("계좌: 110-123-456789")
        assert "110-" in result
        assert "789" in result
    
    def test_mask_dict(self):
        """딕셔너리 마스킹"""
        data = {
            "name": "김철수",
            "ssn": "900101-1234567",
            "email": "kim@test.com",
            "nested": {
                "phone": "010-1234-5678"
            }
        }
        
        result = DataMasker.mask_dict(data)
        
        assert result["name"] == "김철수"  # 일반 텍스트는 그대로
        assert result["ssn"] == "******-*******"
        assert "k" in result["email"]
        assert result["nested"]["phone"] == "010-****-5678"
    
    def test_mask_list(self):
        """리스트 마스킹"""
        data = [
            "일반 텍스트",
            "주민번호: 900101-1234567",
            {"card": "1234-5678-9012-3456"}
        ]
        
        result = DataMasker.mask_list(data)
        
        assert result[0] == "일반 텍스트"
        assert "******-*******" in result[1]
        assert "****-****-****-3456" in result[2]["card"]
    
    def test_mask_response_json_string(self):
        """JSON 문자열 응답 마스킹"""
        json_str = '{"ssn": "900101-1234567", "name": "홍길동"}'
        
        result = DataMasker.mask_response(json_str)
        
        assert result["ssn"] == "******-*******"
        assert result["name"] == "홍길동"
    
    def test_mask_empty_values(self):
        """빈 값 처리"""
        assert DataMasker.mask_string(None) is None
        assert DataMasker.mask_string("") == ""
        assert DataMasker.mask_dict(None) is None
        assert DataMasker.mask_dict({}) == {}
        assert DataMasker.mask_list(None) is None
        assert DataMasker.mask_list([]) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
