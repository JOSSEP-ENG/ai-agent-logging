'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { MCPConnectionsTab } from '@/components/settings/MCPConnectionsTab';
import { PermissionsTab } from '@/components/settings/PermissionsTab';

type SettingsTab = 'connections' | 'permissions';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('connections');

  // 탭별 컴포넌트 렌더링
  const renderTabContent = () => {
    switch (activeTab) {
      case 'connections':
        return <MCPConnectionsTab />;
      case 'permissions':
        return <PermissionsTab />;
      default:
        return <MCPConnectionsTab />;
    }
  };

  return (
    <PageLayout
      pageKey="/settings"
      currentTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as SettingsTab)}
    >
      {renderTabContent()}
    </PageLayout>
  );
}
