'use client';

export function SecurityTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">보안 설정</h2>
        <p className="text-dark-400 text-sm">
          계정 보안 및 접근 권한을 관리합니다.
        </p>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="w-16 h-16 bg-dark-700 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-dark-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">준비 중</h3>
          <p className="text-dark-400 text-sm">
            보안 설정 기능은 현재 개발 중입니다.
            <br />
            곧 사용할 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
