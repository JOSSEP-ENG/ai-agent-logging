'use client';

import { useState } from 'react';
import { Shield, Smartphone, Clock, Save, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui';

export function SecurityTab() {
  const [settings, setSettings] = useState({
    twoFactorAuth: false,
    sessionTimeout: '30',
    loginAlerts: true,
  });

  const handleSave = async () => {
    try {
      // TODO: API로 보안 설정 저장
      console.log('Saving security settings:', settings);
    } catch (error) {
      console.error('Failed to save security settings:', error);
    }
  };

  const toggleTwoFactor = () => {
    setSettings((prev) => ({ ...prev, twoFactorAuth: !prev.twoFactorAuth }));
  };

  const toggleLoginAlerts = () => {
    setSettings((prev) => ({ ...prev, loginAlerts: !prev.loginAlerts }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">보안 설정</h2>
        <p className="text-dark-400">
          계정 보안을 강화하기 위한 설정을 관리합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 2단계 인증 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <Smartphone className="w-5 h-5 text-accent-400" />
                <div>
                  <p className="font-medium text-white">2단계 인증</p>
                  <p className="text-sm text-dark-400">
                    로그인 시 추가 인증을 요구합니다
                  </p>
                </div>
              </div>
              <button
                onClick={toggleTwoFactor}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.twoFactorAuth ? 'bg-accent-500' : 'bg-dark-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.twoFactorAuth ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {settings.twoFactorAuth && (
              <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <div className="flex gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-yellow-400">
                    2단계 인증을 활성화하려면 인증 앱을 설정해야 합니다.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 세션 타임아웃 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Clock className="w-4 h-4" />
              세션 타임아웃 (분)
            </label>
            <select
              value={settings.sessionTimeout}
              onChange={(e) =>
                setSettings({ ...settings, sessionTimeout: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="15">15분</option>
              <option value="30">30분</option>
              <option value="60">1시간</option>
              <option value="120">2시간</option>
              <option value="1440">24시간</option>
            </select>
            <p className="text-xs text-dark-500 mt-1">
              일정 시간 동안 활동이 없으면 자동으로 로그아웃됩니다.
            </p>
          </div>

          {/* 로그인 알림 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">로그인 알림</p>
                <p className="text-sm text-dark-400">
                  새로운 로그인이 감지되면 알림을 받습니다
                </p>
              </div>
            </div>
            <button
              onClick={toggleLoginAlerts}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.loginAlerts ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.loginAlerts ? 'translate-x-6' : 'translate-x-1'
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