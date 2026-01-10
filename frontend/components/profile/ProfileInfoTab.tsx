'use client';

import { useState } from 'react';
import { User, Mail, Briefcase, Calendar, Save } from 'lucide-react';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/lib/store';

export function ProfileInfoTab() {
  const { user } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    role: user?.role || 'user',
  });

  const handleSave = async () => {
    try {
      // TODO: API로 프로필 업데이트 요청
      console.log('Saving profile:', formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return '관리자';
      case 'auditor':
        return '감사자';
      default:
        return '일반 사용자';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">프로필 정보</h2>
        <p className="text-dark-400">내 정보를 확인하고 수정할 수 있습니다.</p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <div className="space-y-6">
          {/* 이름 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <User className="w-4 h-4" />
              이름
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white focus:outline-none focus:border-accent-500 transition-colors"
              />
            ) : (
              <p className="text-white">{user?.name || '-'}</p>
            )}
          </div>

          {/* 이메일 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Mail className="w-4 h-4" />
              이메일
            </label>
            <p className="text-white">{user?.email || '-'}</p>
            <p className="text-xs text-dark-500 mt-1">
              이메일은 변경할 수 없습니다.
            </p>
          </div>

          {/* 역할 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Briefcase className="w-4 h-4" />
              역할
            </label>
            <p className="text-white">{getRoleLabel(user?.role || 'user')}</p>
            <p className="text-xs text-dark-500 mt-1">
              역할은 관리자만 변경할 수 있습니다.
            </p>
          </div>

          {/* 가입일 */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-dark-300 mb-2">
              <Calendar className="w-4 h-4" />
              가입일
            </label>
            <p className="text-white">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('ko-KR')
                : '-'}
            </p>
          </div>

          {/* 버튼 */}
          <div className="flex gap-2 pt-4 border-t border-dark-700">
            {isEditing ? (
              <>
                <Button
                  onClick={handleSave}
                  variant="primary"
                  size="sm"
                  className="gap-2"
                >
                  <Save className="w-4 h-4" />
                  저장
                </Button>
                <Button
                  onClick={() => {
                    setIsEditing(false);
                    setFormData({
                      name: user?.name || '',
                      email: user?.email || '',
                      role: user?.role || 'user',
                    });
                  }}
                  variant="secondary"
                  size="sm"
                >
                  취소
                </Button>
              </>
            ) : (
              <Button
                onClick={() => setIsEditing(true)}
                variant="secondary"
                size="sm"
              >
                수정
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
