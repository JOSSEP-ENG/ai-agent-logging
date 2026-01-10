'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Menu,
  Bot,
  Plus,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { GLOBAL_MENU, filterMenuByRole } from '@/lib/navigation';
import { SessionList } from './SessionList';
import { UserMenu } from './UserMenu';
import { Button } from '@/components/ui';

export function GlobalSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuthStore();

  const [isExpanded, setIsExpanded] = useState(true);
  const [sessionRefresh, setSessionRefresh] = useState(0);

  // localStorage에서 토글 상태 로드
  useEffect(() => {
    const saved = localStorage.getItem('sidebar-expanded');
    if (saved !== null) setIsExpanded(saved === 'true');
  }, []);

  // 토글 상태 저장
  useEffect(() => {
    localStorage.setItem('sidebar-expanded', isExpanded.toString());
  }, [isExpanded]);

  // 권한 기반 필터링
  const visibleItems = filterMenuByRole(GLOBAL_MENU, user?.role || 'user');

  // 현재 세션 ID 추출
  const currentSessionId = searchParams.get('session') || undefined;

  // 새 대화 시작
  const handleNewChat = () => {
    router.push('/chat');
    setSessionRefresh(prev => prev + 1);
  };

  // 활성 메뉴 확인
  const isActiveMenu = (href: string) => {
    if (href.includes('?')) {
      const [path, query] = href.split('?');
      return pathname === path && searchParams.toString().includes(query);
    }
    return pathname === href;
  };

  return (
    <aside
      className={cn(
        'h-screen bg-dark-900 border-r border-dark-800 flex flex-col transition-all duration-300',
        isExpanded ? 'w-64' : 'w-16'
      )}
    >
      {/* 헤더 */}
      <div className="p-4 border-b border-dark-800">
        <div className="flex items-center gap-3 mb-3">
          {/* 토글 버튼 */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5 text-dark-400" />
          </button>

          {/* 로고 (펼쳤을 때만) */}
          {isExpanded && (
            <>
              <div className="w-8 h-8 bg-accent-500 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="font-semibold text-white">AI Platform</span>
            </>
          )}
        </div>

        {/* 새 대화 버튼 */}
        {isAuthenticated && (
          <Button
            onClick={handleNewChat}
            className={cn(
              'w-full justify-start gap-2',
              !isExpanded && 'justify-center px-2'
            )}
            variant="secondary"
            size="sm"
          >
            <Plus className="w-4 h-4" />
            {isExpanded && '새 대화'}
          </Button>
        )}
      </div>

      {/* 메인 메뉴 */}
      <nav className="flex-1 overflow-y-auto p-2">
        {visibleItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = isActiveMenu(item.href);
          const showSeparator = item.separator && index > 0;

          return (
            <div key={item.href}>
              {showSeparator && <div className="h-px bg-dark-800 my-2" />}
              <Link
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                  isActive
                    ? 'bg-accent-500/10 text-accent-400'
                    : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200',
                  !isExpanded && 'justify-center'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {isExpanded && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            </div>
          );
        })}
      </nav>

      {/* 세션 목록 */}
      {isAuthenticated && (
        <SessionList
          isExpanded={isExpanded}
          currentSessionId={currentSessionId}
          onSessionRefresh={sessionRefresh}
        />
      )}

      {/* 사용자 메뉴 */}
      <div className="border-t border-dark-800 p-2">
        {isAuthenticated ? (
          <UserMenu isExpanded={isExpanded} />
        ) : (
          <Link
            href="/auth/login"
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-dark-200 transition-colors',
              !isExpanded && 'justify-center'
            )}
          >
            <Bot className="w-5 h-5" />
            {isExpanded && <span className="text-sm font-medium">로그인</span>}
          </Link>
        )}
      </div>
    </aside>
  );
}
