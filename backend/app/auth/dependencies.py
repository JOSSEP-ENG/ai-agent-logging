"""인증 의존성

FastAPI의 Depends로 사용되는 인증/권한 검사 함수들
"""
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User, UserRole
from app.auth.utils import decode_access_token
from app.auth.service import AuthService


# Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """현재 인증된 사용자 가져오기
    
    Authorization: Bearer <token> 헤더에서 토큰을 추출하고
    유효한 사용자를 반환합니다.
    
    Raises:
        HTTPException 401: 인증 실패
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 디코딩
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 타입 확인 (refresh 토큰은 거부)
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="액세스 토큰을 사용하세요",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 사용자 조회
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(uuid.UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """현재 사용자 가져오기 (선택적)
    
    인증되지 않아도 None을 반환하고 계속 진행합니다.
    인증이 선택적인 엔드포인트에 사용합니다.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(required_role: UserRole):
    """역할 기반 권한 검사 의존성 팩토리
    
    사용 예:
        @router.get("/admin/users")
        async def get_users(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한이 없습니다. {required_role.value} 이상의 권한이 필요합니다.",
            )
        return current_user
    
    return role_checker


# 편의를 위한 미리 정의된 의존성
require_user = require_role(UserRole.USER)
require_auditor = require_role(UserRole.AUDITOR)
require_admin = require_role(UserRole.ADMIN)
