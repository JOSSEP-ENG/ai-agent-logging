"""인증/인가 모듈

JWT 기반 인증 및 역할 기반 권한 관리를 담당합니다.
"""
from .service import AuthService
from .router import router as auth_router
from .dependencies import (
    get_current_user,
    get_current_user_optional,
    require_role,
    require_user,
    require_auditor,
    require_admin,
)
from .utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

__all__ = [
    "AuthService",
    "auth_router",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_user",
    "require_auditor",
    "require_admin",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
]
