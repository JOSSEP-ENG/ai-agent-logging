'use client';

import { useState } from 'react';
import { Database, User, Bell, Shield } from 'lucide-react';
import { MCPConnectionsTab } from '@/components/settings/MCPConnectionsTab';

type SettingsTab = 'mcp' | 'profile' | 'notifications' | 'security';

interface TabItem {
  id: SettingsTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  component: React.ReactNode;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('mcp');

  const tabs: TabItem[] = [
    {
      id: 'mcp',
      label: 'MCP 서버 관리',
      icon: Database,
      component: <MCPConnectionsTab />,
    },
    // {
    //   id: 'profile',
    //   label: '프로필',
    //   icon: User,
    //   component: <div className="text-dark-400">프로필 설정 (준비중)</div>,
    // },
    // {
    //   id: 'notifications',
    //   label: '알림',
    //   icon: Bell,
    //   component: <div className="text-dark-400">알림 설정 (준비중)</div>,
    // },
    // {
    //   id: 'security',
    //   label: '보안',
    //   icon: Shield,
    //   component: <div className="text-dark-400">보안 설정 (준비중)</div>,
    // },
  ];

  const currentTab = tabs.find((tab) => tab.id === activeTab);

  return (
    <div className="min-h-screen bg-dark-900 flex">
      {/* 사이드 메뉴 */}
      <aside className="w-64 border-r border-dark-800 p-4">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">설정</h1>
          <p className="text-dark-500 text-sm">시스템 설정 관리</p>
        </div>

        <nav className="space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left
                  ${
                    isActive
                      ? 'bg-accent-500/10 text-accent-400'
                      : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* 메인 콘텐츠 영역 */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl p-8">
          {currentTab?.component}
        </div>
      </main>
    </div>
  );
}
