'use client';

export function NotificationsTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">알림 설정</h2>
        <p className="text-dark-400 text-sm">
          시스템 알림 및 이메일 알림을 관리합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-dark-700 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">준비 중</h3>
          <p className="text-dark-400 text-sm">
            알림 설정 기능은 현재 개발 중입니다.
            <br />
            곧 사용할 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
