'use client';

export const dynamic = 'force-dynamic';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { hasPageAccess } from '@/lib/navigation';
import { AuditLogsTab } from '@/components/admin/AuditLogsTab';

export default function AuditLogsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, checkAuth } = useAuthStore();

  // 인증 체크
  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 인증 가드
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // 권한 체크
  useEffect(() => {
    if (!authLoading && isAuthenticated && !hasPageAccess('/audit-logs', user?.role || 'user')) {
      router.push('/chat');
    }
  }, [authLoading, isAuthenticated, user, router]);

  // 로딩 중이거나 인증되지 않은 경우
  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-900">
        <div className="text-center">
          <div className="loading-dots mb-4">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <p className="text-dark-400">로딩 중...</p>
        </div>
      </div>
    );
  }

  // 권한 없음
  if (!hasPageAccess('/audit-logs', user?.role || 'user')) {
    return (
      <div className="flex h-screen items-center justify-center bg-dark-900">
        <div className="text-center">
          <p className="text-red-400 text-lg">접근 권한이 없습니다.</p>
          <p className="text-dark-500 text-sm mt-2">
            이 페이지에 접근할 수 있는 권한이 없습니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-900">
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* 헤더 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              로그 조회
            </h1>
            <p className="text-dark-400">
              시스템 감사 로그를 조회하고 분석합니다.
            </p>
          </div>

          {/* 로그 조회 내용 */}
          <AuditLogsTab />
        </div>
      </div>
    </div>
  );
}
