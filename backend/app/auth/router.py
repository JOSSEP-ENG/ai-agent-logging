"""인증 API 라우터

회원가입, 로그인, 사용자 관리 API
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db
from app.models.user import User, UserRole
from app.auth.service import AuthService
from app.auth.dependencies import (
    get_current_user,
    require_role,
    require_admin,
)
from app.auth.utils import decode_access_token, create_access_token


router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ============ Pydantic 스키마 ============

class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="최소 8자")
    name: str = Field(..., min_length=2, max_length=100)


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """사용자 응답"""
    id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    users: List[UserResponse]
    total: int


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UpdateRoleRequest(BaseModel):
    """역할 변경 요청"""
    role: str = Field(..., pattern="^(user|auditor|admin)$")


# ============ 인증 API ============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """회원가입
    
    새 사용자를 등록합니다. 기본 역할은 USER입니다.
    """
    auth_service = AuthService(db)
    
    user, error = await auth_service.register(
        email=request.email,
        password=request.password,
        name=request.name,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """로그인
    
    이메일과 비밀번호로 로그인하고 JWT 토큰을 발급받습니다.
    """
    auth_service = AuthService(db)
    
    result, error = await auth_service.login(
        email=request.email,
        password=request.password,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )
    
    return TokenResponse(**result)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """토큰 갱신
    
    리프레시 토큰으로 새 액세스 토큰을 발급받습니다.
    """
    # 리프레시 토큰 검증
    payload = decode_access_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
        )
    
    # 새 액세스 토큰 발급
    auth_service = AuthService(db)
    new_token = await auth_service.refresh_access_token(user_id)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 갱신에 실패했습니다",
        )
    
    return RefreshResponse(access_token=new_token)


# ============ 현재 사용자 API ============

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """현재 사용자 정보 조회"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 변경"""
    auth_service = AuthService(db)
    
    success, error = await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return {"message": "비밀번호가 변경되었습니다"}


# ============ 관리자 API ============

@router.get("/users", response_model=UserListResponse)
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 목록 조회 (Admin 전용)"""
    auth_service = AuthService(db)
    
    users = await auth_service.get_users(
        limit=limit,
        offset=offset,
        active_only=False,
    )
    
    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
            )
            for user in users
        ],
        total=len(users),
    )


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    request: UpdateRoleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 역할 변경 (Admin 전용)"""
    # 자기 자신의 역할은 변경 불가
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 역할은 변경할 수 없습니다",
        )
    
    auth_service = AuthService(db)
    
    new_role = UserRole(request.role)
    user = await auth_service.update_user_role(user_id, new_role)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 비활성화 (Admin 전용)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신을 비활성화할 수 없습니다",
        )
    
    auth_service = AuthService(db)
    user = await auth_service.deactivate_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 활성화 (Admin 전용)"""
    auth_service = AuthService(db)
    user = await auth_service.activate_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
