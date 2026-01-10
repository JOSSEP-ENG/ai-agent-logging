'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store';
import { Clock, MapPin, Monitor } from 'lucide-react';

interface Activity {
  id: string;
  type: 'login' | 'logout' | 'session_created' | 'settings_changed';
  description: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

export function ActivityHistoryTab() {
  const { user } = useAuthStore();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // TODO: API에서 활동 기록 로드
    // 현재는 더미 데이터 사용
    setTimeout(() => {
      setActivities([
        {
          id: '1',
          type: 'login',
          description: '로그인',
          timestamp: new Date().toISOString(),
          ip_address: '192.168.1.1',
          user_agent: 'Chrome on Windows',
        },
      ]);
      setIsLoading(false);
    }, 500);
  }, []);

  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'login':
        return '🔓';
      case 'logout':
        return '🔒';
      case 'session_created':
        return '💬';
      case 'settings_changed':
        return '⚙️';
      default:
        return '📝';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">활동 기록</h2>
        <p className="text-dark-400 text-sm">
          최근 로그인 및 계정 활동 내역을 확인합니다.
        </p>
      </div>

      {/* 최근 로그인 정보 */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">최근 로그인</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3 text-dark-300">
            <Clock className="w-4 h-4 text-dark-500" />
            <span>마지막 로그인: {user?.last_login_at ? formatTimestamp(user.last_login_at) : '정보 없음'}</span>
          </div>
          <div className="flex items-center gap-3 text-dark-300">
            <MapPin className="w-4 h-4 text-dark-500" />
            <span>IP 주소: 192.168.1.1</span>
          </div>
          <div className="flex items-center gap-3 text-dark-300">
            <Monitor className="w-4 h-4 text-dark-500" />
            <span>디바이스: Chrome on Windows</span>
          </div>
        </div>
      </div>

      {/* 활동 내역 */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">활동 내역</h3>

        {isLoading ? (
          <div className="text-center py-8">
            <div className="inline-block w-8 h-8 border-4 border-dark-600 border-t-accent-500 rounded-full animate-spin" />
            <p className="text-dark-400 text-sm mt-3">로딩 중...</p>
          </div>
        ) : activities.length > 0 ? (
          <div className="space-y-3">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 bg-dark-900 rounded-lg border border-dark-700"
              >
                <span className="text-2xl">{getActivityIcon(activity.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium">{activity.description}</p>
                  <p className="text-dark-400 text-xs mt-1">
                    {formatTimestamp(activity.timestamp)}
                  </p>
                  {activity.ip_address && (
                    <p className="text-dark-500 text-xs mt-1">
                      IP: {activity.ip_address}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-dark-400 text-sm">활동 내역이 없습니다.</p>
          </div>
        )}
      </div>

      {/* 계정 정보 */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">계정 정보</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-dark-400">계정 생성일</span>
            <span className="text-white">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString('ko-KR') : '정보 없음'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">계정 상태</span>
            <span className={user?.is_active ? 'text-green-400' : 'text-red-400'}>
              {user?.is_active ? '활성' : '비활성'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-400">역할</span>
            <span className="text-white">
              {user?.role === 'admin' ? '관리자' : user?.role === 'auditor' ? '감사자' : '사용자'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
