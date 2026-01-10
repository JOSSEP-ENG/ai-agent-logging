'use client';

import { useState } from 'react';
import { Settings, Save, Bot } from 'lucide-react';
import { Button } from '@/components/ui';

export function GeneralTab() {
  const [settings, setSettings] = useState({
    defaultAgent: 'claude-sonnet-4',
    autoSave: true,
    confirmActions: true,
  });

  const handleSave = async () => {
    try {
      console.log('Saving general settings:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const toggleAutoSave = () => {
    setSettings(prev => ({ ...prev, autoSave: !prev.autoSave }));
  };

  const toggleConfirmActions = () => {
    setSettings(prev => ({ ...prev, confirmActions: !prev.confirmActions }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">일반 설정</h2>
        <p className="text-dark-400">
          시스템 기본 동작 및 환경을 설정합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 기본 에이전트 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Bot className="w-4 h-4" />
              기본 AI 모델
            </label>
            <select
              value={settings.defaultAgent}
              onChange={(e) =>
                setSettings({ ...settings, defaultAgent: e.target.value })
              }
              className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
            >
              <option value="claude-sonnet-4">Claude Sonnet 4</option>
              <option value="claude-opus-4">Claude Opus 4</option>
              <option value="claude-haiku">Claude Haiku</option>
            </select>
            <p className="text-xs text-dark-500 mt-1">
              새 채팅 시작 시 기본으로 사용할 AI 모델을 선택합니다.
            </p>
          </div>

          {/* 자동 저장 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">자동 저장</p>
                <p className="text-sm text-dark-400">
                  대화 내용을 자동으로 저장합니다
                </p>
              </div>
            </div>
            <button
              onClick={toggleAutoSave}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.autoSave ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* 작업 확인 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="w-5 h-5 text-accent-400" />
              <div>
                <p className="font-medium text-white">작업 확인</p>
                <p className="text-sm text-dark-400">
                  중요한 작업 수행 전 확인 메시지를 표시합니다
                </p>
              </div>
            </div>
            <button
              onClick={toggleConfirmActions}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.confirmActions ? 'bg-accent-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.confirmActions ? 'translate-x-6' : 'translate-x-1'
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
