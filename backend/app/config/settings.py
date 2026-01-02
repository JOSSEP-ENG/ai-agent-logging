from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "AI Platform"
    debug: bool = True
    
    # Database (PostgreSQL for audit logs)
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_platform"
    
    # MySQL MCP 연결 정보
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = ""
    
    # Gemini API (2단계)
    gemini_api_key: str = ""
    
    # 암호화 키 (민감정보 저장용)
    encryption_key: str = "your-32-byte-encryption-key-here"
    
    # 세션 설정
    session_expire_hours: int = 24
    
    # 감사 로그 설정
    audit_log_retention_days: int = 90
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
