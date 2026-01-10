'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, MessageSquare, Trash2, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { chatApi, Session } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store';

const SESSIONS_PER_PAGE = 10;

export default function ChatHistoryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading, checkAuth } = useAuthStore();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

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

  // 세션 로드
  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, searchQuery, isAuthenticated]);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const offset = (currentPage - 1) * SESSIONS_PER_PAGE;
      const response = await chatApi.getSessions(SESSIONS_PER_PAGE, offset);
      setSessions(response.sessions);
      setTotalSessions(response.total || response.sessions.length);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();

    if (!confirm('이 대화를 삭제하시겠습니까?')) return;

    try {
      await chatApi.deleteSession(sessionId);
      loadSessions();
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/chat?session=${sessionId}`);
  };

  const totalPages = Math.ceil(totalSessions / SESSIONS_PER_PAGE);

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

  return (
    <div className="min-h-screen bg-dark-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 text-dark-400 hover:text-dark-200 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            채팅으로 돌아가기
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">채팅 히스토리</h1>
          <p className="text-dark-400">
            전체 대화 내역을 조회하고 관리할 수 있습니다.
          </p>
        </div>

        {/* 검색 */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="대화 검색..."
              className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500 transition-colors"
            />
          </div>
        </div>

        {/* 세션 목록 */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <p className="text-dark-400 text-lg">
              {searchQuery ? '검색 결과가 없습니다.' : '대화 내역이 없습니다.'}
            </p>
            <p className="text-dark-500 text-sm mt-2">
              새로운 대화를 시작해보세요.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => handleSessionClick(session.id)}
                className="group bg-dark-800 border border-dark-700 rounded-lg p-4 hover:border-accent-500/50 transition-colors cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <MessageSquare className="w-5 h-5 text-dark-500 flex-shrink-0 mt-1" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-white font-medium mb-1 truncate">
                      {session.title || '새 대화'}
                    </h3>
                    <p className="text-dark-400 text-sm">
                      마지막 업데이트: {formatDate(session.updated_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, session.id)}
                    className="opacity-0 group-hover:opacity-100 p-2 hover:bg-dark-700 rounded-lg transition-all"
                  >
                    <Trash2 className="w-4 h-4 text-dark-500 hover:text-error" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 페이징 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage === 1
                  ? 'text-dark-600 cursor-not-allowed'
                  : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
              )}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                // 현재 페이지 주변만 표시
                if (
                  page === 1 ||
                  page === totalPages ||
                  (page >= currentPage - 2 && page <= currentPage + 2)
                ) {
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={cn(
                        'px-3 py-1 rounded-lg text-sm transition-colors',
                        page === currentPage
                          ? 'bg-accent-500 text-white'
                          : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
                      )}
                    >
                      {page}
                    </button>
                  );
                } else if (
                  page === currentPage - 3 ||
                  page === currentPage + 3
                ) {
                  return (
                    <span key={page} className="text-dark-600 px-1">
                      ...
                    </span>
                  );
                }
                return null;
              })}
            </div>

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage === totalPages
                  ? 'text-dark-600 cursor-not-allowed'
                  : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
              )}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* 통계 */}
        {totalSessions > 0 && (
          <div className="text-center mt-6 text-dark-500 text-sm">
            전체 {totalSessions}개의 대화 중 {(currentPage - 1) * SESSIONS_PER_PAGE + 1}-
            {Math.min(currentPage * SESSIONS_PER_PAGE, totalSessions)}개 표시
          </div>
        )}
      </div>
    </div>
  );
}
