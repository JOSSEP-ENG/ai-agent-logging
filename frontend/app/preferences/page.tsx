'use client';

import { useState } from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { GeneralTab } from '@/components/preferences/GeneralTab';
import { AppearanceTab } from '@/components/preferences/AppearanceTab';
import { LanguageTab } from '@/components/preferences/LanguageTab';

type PreferencesTab = 'general' | 'appearance' | 'language';

export default function PreferencesPage() {
  const [activeTab, setActiveTab] = useState<PreferencesTab>('general');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return <GeneralTab />;
      case 'appearance':
        return <AppearanceTab />;
      case 'language':
        return <LanguageTab />;
      default:
        return <GeneralTab />;
    }
  };

  return (
    <PageLayout
      pageKey="/preferences"
      currentTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as PreferencesTab)}
    >
      {renderTabContent()}
    </PageLayout>
  );
}
