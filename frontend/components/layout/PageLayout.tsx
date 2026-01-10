'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { PAGE_CONFIGS, hasPageAccess, filterTabsByRole } from '@/lib/navigation';
import { cn } from '@/lib/utils';

interface QuickLink {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface PageLayoutProps {
  pageKey: string;
  currentTab?: string;
  onTabChange?: (tabId: string) => void;
  quickLinks?: QuickLink[];
  children: React.ReactNode;
}

export function PageLayout({ 
  pageKey, 
  currentTab, 
  onTabChange, 
  quickLinks,
  children 
}: PageLayoutProps) {
  const { user } = useAuthStore();
  const config = PAGE_CONFIGS[pageKey];

  // 페이지 설정이 없으면 에러
  if (!config) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-900">
        <div className="text-center">
          <p className="text-red-400 text-lg">페이지 설정을 찾을 수 없습니다.</p>
          <p className="text-dark-500 text-sm mt-2">페이지 키: {pageKey}</p>
        </div>
      </div>
    );
  }

  // 권한 체크
  if (!hasPageAccess(pageKey, user?.role || 'user')) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-900">
        <div className="text-center">
          <p className="text-red-400 text-lg">접근 권한이 없습니다.</p>
          <p className="text-dark-500 text-sm mt-2">이 페이지에 접근할 수 있는 권한이 없습니다.</p>
        </div>
      </div>
    );
  }

  // 권한에 따라 탭 필터링
  const visibleTabs = config.tabs 
    ? filterTabsByRole(config.tabs, user?.role || 'user')
    : [];

  return (
    <div className="min-h-screen bg-dark-900 flex">
      {/* 로컬 사이드바 */}
      <aside className="w-64 border-r border-dark-800 p-4 flex flex-col">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">{config.title}</h1>
          {config.description && (
            <p className="text-dark-500 text-sm">{config.description}</p>
          )}
        </div>

        {/* 탭 메뉴 */}
        {visibleTabs.length > 0 && (
          <nav className="space-y-1 flex-1">
            {visibleTabs.map(tab => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange?.(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left',
                    isActive
                      ? 'bg-accent-500/10 text-accent-400'
                      : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        )}

        {/* Quick Links */}
        {quickLinks && quickLinks.length > 0 && (
          <div className="pt-4 border-t border-dark-800 space-y-1">
            {quickLinks.map(link => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-dark-200 transition-colors"
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{link.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto">
        <div className={cn(
          'p-8',
          pageKey === '/admin' ? 'max-w-7xl' : 'max-w-5xl'
        )}>
          {children}
        </div>
      </main>
    </div>
  );
}
