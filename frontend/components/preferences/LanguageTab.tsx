'use client';

import { useState } from 'react';
import { Globe, Save, Clock } from 'lucide-react';
import { Button } from '@/components/ui';

export function LanguageTab() {
  const [settings, setSettings] = useState({
    language: 'ko',
    timezone: 'Asia/Seoul',
    dateFormat: 'YYYY-MM-DD',
  });

  const handleSave = async () => {
    try {
      console.log('Saving language settings:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">언어 및 지역</h2>
        <p className="text-dark-400">
          언어, 시간대 및 날짜 형식을 설정합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 언어 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Globe className="w-4 h-4" />
              언어
            </label>
            <select
              value={settings.language}
              onChange={(e) =>
                setSettings({ ...settings, language: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="ko">한국어</option>
              <option value="en">English</option>
              <option value="ja">日本語</option>
              <option value="zh">中文</option>
            </select>
          </div>

          {/* 시간대 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Clock className="w-4 h-4" />
              시간대
            </label>
            <select
              value={settings.timezone}
              onChange={(e) =>
                setSettings({ ...settings, timezone: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="Asia/Seoul">서울 (GMT+9)</option>
              <option value="America/New_York">뉴욕 (GMT-5)</option>
              <option value="Europe/London">런던 (GMT+0)</option>
              <option value="Asia/Tokyo">도쿄 (GMT+9)</option>
            </select>
          </div>

          {/* 날짜 형식 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              날짜 형식
            </label>
            <select
              value={settings.dateFormat}
              onChange={(e) =>
                setSettings({ ...settings, dateFormat: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="YYYY-MM-DD">2025-01-10</option>
              <option value="MM/DD/YYYY">01/10/2025</option>
              <option value="DD/MM/YYYY">10/01/2025</option>
            </select>
          </div>

          {/* 저장 버튼 */}
          <div className="flex gap-2 pt-4 border-t border-dark-700">
            <Button
              onClick={handleSave}
              variant="primary"
              size="sm"
              className="gap-2"
            >
              <Save className="w-4 h-4" />
              저장
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
