"""관리자 모듈

대시보드, 통계, 시스템 설정 관리를 담당합니다.
"""
from .service import AdminService
from .router import router as admin_router

__all__ = [
    "AdminService",
    "admin_router",
]
