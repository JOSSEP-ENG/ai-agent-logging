'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Plus,
  MessageSquare,
  Settings,
  User,
  LogOut,
  Database,
  Shield,
  ChevronRight,
  Trash2,
  Bot,
} from 'lucide-react';
import { Button } from '@/components/ui';
import { chatApi, Session } from '@/lib/api';
import { formatDate, truncate } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store';

interface ChatSidebarProps {
  currentSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  onSessionsRefresh?: number;
}

export function ChatSidebar({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  onSessionsRefresh,
}: ChatSidebarProps) {
  const router = useRouter();
  const { isAuthenticated, user, logout, checkAuth } = useAuthStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 로그인 상태에 따라 세션 로드
  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    } else {
      setSessions([]);
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // 외부에서 새로고침 요청 시 세션 로드
  useEffect(() => {
    if (onSessionsRefresh !== undefined && onSessionsRefresh > 0 && isAuthenticated) {
      loadSessions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onSessionsRefresh]);
  
  const loadSessions = async () => {
    try {
      const response = await chatApi.getSessions(20);
      setSessions(response.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();

    if (!confirm('이 대화를 삭제하시겠습니까?')) return;

    try {
      await chatApi.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));

      if (currentSessionId === sessionId) {
        onNewChat();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };
  
  return (
    <aside className="w-72 h-screen bg-dark-900 border-r border-dark-800 flex flex-col">
      {/* 헤더 */}
      <div className="p-4 border-b border-dark-800">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 bg-accent-500 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <span className="font-semibold text-white">AI Platform</span>
        </div>
        
        <Button 
          onClick={onNewChat}
          className="w-full justify-start gap-2"
          variant="secondary"
        >
          <Plus className="w-4 h-4" />
          새 대화
        </Button>
      </div>
      
      {/* 세션 목록 */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-32 text-dark-500">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-dark-500">
            <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-50" />
            <p className="text-sm">대화 내역이 없습니다</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onSessionSelect(session.id)}
              className={cn(
                'group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer',
                'hover:bg-dark-800 transition-colors',
                currentSessionId === session.id && 'bg-dark-800'
              )}
            >
              <MessageSquare className="w-4 h-4 text-dark-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-dark-200 truncate">
                  {session.title || '새 대화'}
                </p>
                <p className="text-xs text-dark-500">
                  {formatDate(session.updated_at)}
                </p>
              </div>
              <button
                onClick={(e) => handleDelete(e, session.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-dark-700 rounded transition-opacity"
              >
                <Trash2 className="w-4 h-4 text-dark-500 hover:text-error" />
              </button>
            </div>
          ))
        )}
      </div>
      
      {/* 하단 메뉴 */}
      <div className="p-2 border-t border-dark-800 space-y-1">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-dark-800 transition-colors text-dark-400 hover:text-dark-200"
        >
          <Settings className="w-4 h-4" />
          <span className="text-sm">설정</span>
        </Link>

        <Link
          href="/admin"
          className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-dark-800 transition-colors text-dark-400 hover:text-dark-200"
        >
          <Shield className="w-4 h-4" />
          <span className="text-sm">관리자</span>
        </Link>

        {isAuthenticated ? (
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-dark-800 transition-colors text-dark-400 hover:text-dark-200"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">로그아웃</span>
          </button>
        ) : (
          <Link
            href="/auth/login"
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-dark-800 transition-colors text-dark-400 hover:text-dark-200"
          >
            <User className="w-4 h-4" />
            <span className="text-sm">로그인</span>
          </Link>
        )}
      </div>
    </aside>
  );
}
