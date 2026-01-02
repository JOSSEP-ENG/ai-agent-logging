"""인증 서비스

회원가입, 로그인, 사용자 관리를 담당합니다.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User, UserRole
from app.auth.utils import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    """인증 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ 회원가입 ============
    
    async def register(
        self,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.USER,
    ) -> Tuple[Optional[User], Optional[str]]:
        """회원가입
        
        Returns:
            (User, None): 성공
            (None, error_message): 실패
        """
        # 이메일 중복 확인
        existing = await self.get_user_by_email(email)
        if existing:
            return None, "이미 등록된 이메일입니다"
        
        # 비밀번호 해싱
        password_hash = hash_password(password)
        
        # 사용자 생성
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user, None
    
    # ============ 로그인 ============
    
    async def login(
        self,
        email: str,
        password: str,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """로그인
        
        Returns:
            (tokens_dict, None): 성공 - {"access_token": ..., "refresh_token": ..., "user": ...}
            (None, error_message): 실패
        """
        # 사용자 조회
        user = await self.get_user_by_email(email)
        if not user:
            return None, "이메일 또는 비밀번호가 올바르지 않습니다"
        
        # 비밀번호 확인
        if not verify_password(password, user.password_hash):
            return None, "이메일 또는 비밀번호가 올바르지 않습니다"
        
        # 계정 활성화 확인
        if not user.is_active:
            return None, "비활성화된 계정입니다"
        
        # 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # 토큰 생성
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )
        refresh_token = create_refresh_token(str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
            },
        }, None
    
    async def refresh_access_token(
        self,
        user_id: str,
    ) -> Optional[str]:
        """액세스 토큰 갱신"""
        user = await self.get_user_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            return None
        
        return create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )
    
    # ============ 사용자 조회 ============
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """ID로 사용자 조회"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_users(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[User]:
        """사용자 목록 조회 (Admin용)"""
        query = select(User)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # ============ 사용자 관리 (Admin) ============
    
    async def update_user_role(
        self,
        user_id: uuid.UUID,
        new_role: UserRole,
    ) -> Optional[User]:
        """사용자 역할 변경 (Admin용)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def deactivate_user(
        self,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """사용자 비활성화 (Admin용)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def activate_user(
        self,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """사용자 활성화 (Admin용)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """비밀번호 변경

        Returns:
            (True, None): 성공
            (False, error_message): 실패
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False, "사용자를 찾을 수 없습니다"

        # 현재 비밀번호 확인
        if not verify_password(current_password, user.password_hash):
            return False, "현재 비밀번호가 올바르지 않습니다"

        # 새 비밀번호 설정
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        return True, None
