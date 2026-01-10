'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { MessageSquare, Trash2, ChevronDown, List } from 'lucide-react';
import { chatApi, Session } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface SessionListProps {
  isExpanded: boolean;
  currentSessionId?: string;
  onSessionRefresh?: number;
}

export function SessionList({ isExpanded, currentSessionId, onSessionRefresh }: SessionListProps) {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isSessionsExpanded, setIsSessionsExpanded] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // localStorage에서 접기/펼치기 상태 로드
  useEffect(() => {
    const saved = localStorage.getItem('sessions-expanded');
    if (saved !== null) setIsSessionsExpanded(saved === 'true');
  }, []);

  // 접기/펼치기 상태 저장
  useEffect(() => {
    localStorage.setItem('sessions-expanded', isSessionsExpanded.toString());
  }, [isSessionsExpanded]);

  // 세션 로드
  useEffect(() => {
    loadSessions();
  }, [onSessionRefresh]);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const response = await chatApi.getSessions(10); // 최대 10개
      setSessions(response.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/chat?session=${sessionId}`);
  };

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();

    if (!confirm('이 대화를 삭제하시겠습니까?')) return;

    try {
      await chatApi.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));

      // 현재 세션이 삭제되면 새 대화로 이동
      if (currentSessionId === sessionId) {
        router.push('/chat');
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  if (!isExpanded) return null;

  return (
    <div className="border-t border-dark-800">
      {/* 헤더 */}
      <button
        onClick={() => setIsSessionsExpanded(!isSessionsExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 text-dark-400 hover:bg-dark-800 transition-colors"
      >
        <span className="text-xs font-medium">최근 대화</span>
        <ChevronDown
          className={cn(
            'w-4 h-4 transition-transform',
            isSessionsExpanded && 'rotate-180'
          )}
        />
      </button>

      {/* 세션 목록 */}
      {isSessionsExpanded && (
        <div className="px-2 pb-2">
          <div className="max-h-48 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-4 text-dark-500">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-4 text-dark-500 text-xs">
                대화 내역이 없습니다
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSessionClick(session.id)}
                  className={cn(
                    'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors',
                    'hover:bg-dark-700',
                    currentSessionId === session.id && 'bg-dark-700'
                  )}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-dark-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-dark-200 truncate">
                      {session.title || '새 대화'}
                    </p>
                    <p className="text-xs text-dark-500">
                      {formatDate(session.updated_at)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, session.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-dark-600 rounded transition-opacity"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-dark-500 hover:text-error" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* 모두 보기 버튼 */}
          {sessions.length > 0 && (
            <Link
              href="/chat/history"
              className="flex items-center justify-center gap-2 px-3 py-2 mt-2 rounded-lg text-xs text-dark-400 hover:bg-dark-700 hover:text-dark-200 transition-colors"
            >
              <List className="w-3.5 h-3.5" />
              모두 보기
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
