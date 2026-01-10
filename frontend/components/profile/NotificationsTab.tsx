'use client';

import { useState } from 'react';
import { Bell, Mail, MessageSquare, AlertTriangle, Save } from 'lucide-react';
import { Button } from '@/components/ui';

export function NotificationsTab() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    chatNotifications: true,
    systemAlerts: true,
    securityAlerts: true,
  });

  const handleSave = async () => {
    try {
      // TODO: API로 알림 설정 저장
      console.log('Saving notification settings:', settings);
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  };

  const toggleSetting = (key: keyof typeof settings) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">알림 설정</h2>
        <p className="text-dark-400">
          알림 수신 방법과 유형을 설정할 수 있습니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-4">
          {/* 이메일 알림 */}
          <div className="flex items-center justify-between p-4 bg-dark-900 border border-dark-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">이메일 알림</p>
                <p className="text-sm text-dark-400">
                  중요한 이벤트를 이메일로 받습니다
                </p>
              </div>
            </div>
            <button
              onClick={() => toggleSetting('emailNotifications')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.emailNotifications ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.emailNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* 채팅 알림 */}
          <div className="flex items-center justify-between p-4 bg-dark-900 border border-dark-700 rounded-lg">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">채팅 알림</p>
                <p className="text-sm text-dark-400">
                  새로운 메시지 알림을 받습니다
                </p>
              </div>
            </div>
            <button
              onClick={() => toggleSetting('chatNotifications')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.chatNotifications ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.chatNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* 시스템 알림 */}
          <div className="flex items-center justify-between p-4 bg-dark-900 border border-dark-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">시스템 알림</p>
                <p className="text-sm text-dark-400">
                  시스템 업데이트 및 공지사항을 받습니다
                </p>
              </div>
            </div>
            <button
              onClick={() => toggleSetting('systemAlerts')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.systemAlerts ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.systemAlerts ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* 보안 알림 */}
          <div className="flex items-center justify-between p-4 bg-dark-900 border border-dark-700 rounded-lg">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">보안 알림</p>
                <p className="text-sm text-dark-400">
                  로그인 및 보안 관련 알림을 받습니다
                </p>
              </div>
            </div>
            <button
              onClick={() => toggleSetting('securityAlerts')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.securityAlerts ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.securityAlerts ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
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