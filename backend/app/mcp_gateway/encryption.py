"""MCP 연결 인증정보 암호화 서비스

Fernet 대칭 암호화를 사용하여 민감한 인증정보를 안전하게 저장합니다.
"""
import json
import base64
from cryptography.fernet import Fernet
from app.config import get_settings


class EncryptionService:
    """Fernet 기반 대칭 암호화 서비스"""

    def __init__(self):
        settings = get_settings()
        # 환경변수에서 Fernet 키 로드 (32 bytes base64)
        encryption_key = settings.encryption_key
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY가 설정되지 않았습니다. "
                ".env 파일에 ENCRYPTION_KEY를 추가해주세요."
            )

        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, data: dict) -> str:
        """딕셔너리를 암호화하여 base64 문자열 반환

        Args:
            data: 암호화할 데이터 (예: {"username": "root", "password": "1234"})

        Returns:
            암호화된 base64 문자열
        """
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted = self.cipher.encrypt(json_bytes)
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, encrypted_str: str) -> dict:
        """암호화된 문자열을 복호화하여 딕셔너리 반환

        Args:
            encrypted_str: 암호화된 base64 문자열

        Returns:
            복호화된 데이터 딕셔너리
        """
        encrypted = base64.b64decode(encrypted_str.encode('utf-8'))
        json_bytes = self.cipher.decrypt(encrypted)
        return json.loads(json_bytes.decode('utf-8'))
