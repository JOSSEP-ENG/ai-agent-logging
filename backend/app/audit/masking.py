import re
import json
from typing import Any, Dict


class DataMasker:
    """민감정보 마스킹 처리
    
    PRD 7장 마스킹 규칙 구현:
    - 주민등록번호: ******-*******
    - 카드번호: ****-****-****-3456
    - 이메일: k**@company.com
    - 전화번호: 010-****-5678
    - 계좌번호: 110-***-***789
    """
    
    # 정규식 패턴
    PATTERNS = {
        # 주민등록번호: 6자리-7자리
        "ssn": (
            r'\b(\d{6})-?(\d{7})\b',
            lambda m: "******-*******"
        ),
        # 카드번호: 4자리-4자리-4자리-4자리
        "card": (
            r'\b(\d{4})-?(\d{4})-?(\d{4})-?(\d{4})\b',
            lambda m: f"****-****-****-{m.group(4)}"
        ),
        # 이메일
        "email": (
            r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            lambda m: f"{m.group(1)[0]}{'*' * (len(m.group(1))-1)}@{m.group(2)}"
        ),
        # 전화번호: 010-1234-5678 또는 01012345678
        "phone": (
            r'\b(01[016789])-?(\d{3,4})-?(\d{4})\b',
            lambda m: f"{m.group(1)}-****-{m.group(3)}"
        ),
        # 계좌번호: 다양한 형식 (간단히 숫자-숫자-숫자 패턴)
        "account": (
            r'\b(\d{3})-(\d{2,6})-(\d{2,6})\b',
            lambda m: f"{m.group(1)}-{'*' * len(m.group(2))}-{'*' * (len(m.group(3))-3)}{m.group(3)[-3:]}"
        ),
    }
    
    @classmethod
    def mask_string(cls, text: str) -> str:
        """문자열 내 민감정보 마스킹"""
        if not text or not isinstance(text, str):
            return text
        
        result = text
        for pattern_name, (pattern, replacer) in cls.PATTERNS.items():
            result = re.sub(pattern, replacer, result)
        
        return result
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리 내 모든 문자열 값 마스킹 (재귀)"""
        if not data:
            return data
        
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked[key] = cls.mask_string(value)
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = cls.mask_list(value)
            else:
                masked[key] = value
        
        return masked
    
    @classmethod
    def mask_list(cls, data: list) -> list:
        """리스트 내 모든 값 마스킹 (재귀)"""
        if not data:
            return data
        
        masked = []
        for item in data:
            if isinstance(item, str):
                masked.append(cls.mask_string(item))
            elif isinstance(item, dict):
                masked.append(cls.mask_dict(item))
            elif isinstance(item, list):
                masked.append(cls.mask_list(item))
            else:
                masked.append(item)
        
        return masked
    
    @classmethod
    def mask_response(cls, response: Any) -> Any:
        """MCP 응답 마스킹 (타입에 따라 처리)"""
        if response is None:
            return None
        
        if isinstance(response, str):
            # JSON 문자열인 경우 파싱 후 처리
            try:
                parsed = json.loads(response)
                masked = cls.mask_dict(parsed) if isinstance(parsed, dict) else cls.mask_list(parsed)
                return masked
            except json.JSONDecodeError:
                return cls.mask_string(response)
        
        if isinstance(response, dict):
            return cls.mask_dict(response)
        
        if isinstance(response, list):
            return cls.mask_list(response)
        
        return response
