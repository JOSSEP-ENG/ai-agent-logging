'use client';

import { Suspense } from 'react';
import { usePathname } from 'next/navigation';
import { GlobalSidebar } from './GlobalSidebar';

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // 사이드바를 표시하지 않을 경로
  const hideSidebarPaths = ['/auth/login', '/auth/register'];
  const shouldHideSidebar = hideSidebarPaths.some(path => pathname.startsWith(path));

  if (shouldHideSidebar) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Suspense fallback={<div className="w-64 bg-dark-900 border-r border-dark-800" />}>
        <GlobalSidebar />
      </Suspense>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
