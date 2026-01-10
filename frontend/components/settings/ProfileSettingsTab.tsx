'use client';

export function ProfileSettingsTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">프로필 설정</h2>
        <p className="text-dark-400 text-sm">
          사용자 프로필 정보를 관리합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-dark-700 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">준비 중</h3>
          <p className="text-dark-400 text-sm">
            프로필 설정 기능은 현재 개발 중입니다.
            <br />
            곧 사용할 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
