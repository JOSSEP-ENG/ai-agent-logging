'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { ProfileInfoTab } from '@/components/profile/ProfileInfoTab';
import { NotificationsTab } from '@/components/profile/NotificationsTab';
import { SecurityTab } from '@/components/profile/SecurityTab';
import { PasswordChangeTab } from '@/components/profile/PasswordChangeTab';

type ProfileTab = 'info' | 'notifications' | 'security' | 'password';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<ProfileTab>('info');

  // 탭별 컴포넌트 렌더링
  const renderTabContent = () => {
    switch (activeTab) {
      case 'info':
        return <ProfileInfoTab />;
      case 'notifications':
        return <NotificationsTab />;
      case 'security':
        return <SecurityTab />;
      case 'password':
        return <PasswordChangeTab />;
      default:
        return <ProfileInfoTab />;
    }
  };

  return (
    <PageLayout
      pageKey="/profile"
      currentTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as ProfileTab)}
    >
      {renderTabContent()}
    </PageLayout>
  );
}

