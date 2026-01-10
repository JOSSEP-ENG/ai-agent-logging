'use client';

import { useState } from 'react';
import { Lock, Eye, EyeOff, Save } from 'lucide-react';
import { Button } from '@/components/ui';

export function PasswordChangeTab() {
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  const handleSave = async () => {
    try {
      // TODO: API로 비밀번호 변경 요청
      console.log('Changing password...');
      setPasswords({ current: '', new: '', confirm: '' });
    } catch (error) {
      console.error('Failed to change password:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">비밀번호 변경</h2>
        <p className="text-dark-400">
          보안을 위해 주기적으로 비밀번호를 변경하세요.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 현재 비밀번호 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Lock className="w-4 h-4" />
              현재 비밀번호
            </label>
            <div className="relative">
              <input
                type={showPasswords.current ? 'text' : 'password'}
                value={passwords.current}
                onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                className="w-full px-4 py-2 pr-12 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
              >
                {showPasswords.current ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* 새 비밀번호 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Lock className="w-4 h-4" />
              새 비밀번호
            </label>
            <div className="relative">
              <input
                type={showPasswords.new ? 'text' : 'password'}
                value={passwords.new}
                onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                className="w-full px-4 py-2 pr-12 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
              >
                {showPasswords.new ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* 새 비밀번호 확인 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Lock className="w-4 h-4" />
              새 비밀번호 확인
            </label>
            <div className="relative">
              <input
                type={showPasswords.confirm ? 'text' : 'password'}
                value={passwords.confirm}
                onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                className="w-full px-4 py-2 pr-12 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
              >
                {showPasswords.confirm ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
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
              비밀번호 변경
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
