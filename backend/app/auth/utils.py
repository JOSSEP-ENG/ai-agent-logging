"""인증 유틸리티

비밀번호 해싱 및 JWT 토큰 관리
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import get_settings

settings = get_settings()

# 비밀번호 해싱 (bcrypt, cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24시간


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 담을 데이터 (sub: user_id 필수)
        expires_delta: 만료 시간 (기본 24시간)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.encryption_key,
        algorithm=ALGORITHM,
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """JWT 토큰 디코딩
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        토큰 페이로드 또는 None (유효하지 않은 경우)
    """
    try:
        payload = jwt.decode(
            token,
            settings.encryption_key,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def create_refresh_token(user_id: str) -> str:
    """리프레시 토큰 생성 (7일)"""
    return create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=7),
    )
