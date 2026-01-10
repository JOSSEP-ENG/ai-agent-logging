'use client';

import { useState } from 'react';
import { Palette, Save, Monitor, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui';

export function AppearanceTab() {
  const [settings, setSettings] = useState({
    theme: 'dark',
    fontSize: 'medium',
    compactMode: false,
  });

  const handleSave = async () => {
    try {
      console.log('Saving appearance settings:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const themes = [
    { value: 'dark', label: '다크', icon: Moon },
    { value: 'light', label: '라이트', icon: Sun },
    { value: 'auto', label: '시스템 설정', icon: Monitor },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">테마 및 표시</h2>
        <p className="text-dark-400">
          화면 테마와 글꼴 크기를 설정합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 테마 선택 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-3">
              <Palette className="w-4 h-4" />
              테마
            </label>
            <div className="grid grid-cols-3 gap-3">
              {themes.map((theme) => {
                const Icon = theme.icon;
                const isSelected = settings.theme === theme.value;
                return (
                  <button
                    key={theme.value}
                    onClick={() => setSettings({ ...settings, theme: theme.value })}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      isSelected
                        ? 'border-accent-500 bg-accent-500/10'
                        : 'border-dark-700 bg-dark-900 hover:border-dark-600'
                    }`}
                  >
                    <Icon className={`w-6 h-6 mx-auto mb-2 ${
                      isSelected
                        ? 'text-accent-400'
                        : 'text-dark-400'
                    }`} />
                    <p className={`text-sm font-medium text-center ${
                      isSelected
                        ? 'text-accent-400'
                        : 'text-dark-300'
                    }`}>
                      {theme.label}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 글꼴 크기 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              글꼴 크기
            </label>
            <select
              value={settings.fontSize}
              onChange={(e) =>
                setSettings({ ...settings, fontSize: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="small">작게</option>
              <option value="medium">보통</option>
              <option value="large">크게</option>
            </select>
          </div>

          {/* 컴팩트 모드 */}
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-white">컴팩트 모드</p>
              <p className="text-sm text-dark-400">
                UI 요소 간격을 줄여 더 많은 정보를 표시합니다
              </p>
            </div>
            <button
              onClick={() =>
                setSettings({ ...settings, compactMode: !settings.compactMode })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.compactMode ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.compactMode ? 'translate-x-6' : 'translate-x-1'
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
