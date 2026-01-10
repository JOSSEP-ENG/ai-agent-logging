'use client';

import { X } from 'lucide-react';
import { Button } from '@/components/ui';
import { formatDateTime } from '@/lib/utils';

interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  session_id?: string;
  user_query?: string;
  tool_name: string;
  tool_params?: any;
  response?: any;
  status: 'success' | 'fail' | 'denied';
  error_message?: string;
  execution_time_ms?: string;
}

interface Props {
  log: AuditLog;
  onClose: () => void;
}

export function AuditLogDetail({ log, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-dark-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-700">
          <h3 className="text-xl font-semibold text-white">로그 상세 정보</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* 콘텐츠 */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-5rem)] space-y-6">
          {/* 기본 정보 */}
          <section>
            <h4 className="text-sm font-medium text-dark-400 mb-3">기본 정보</h4>
            <div className="grid grid-cols-2 gap-4">
              <InfoField label="로그 ID" value={log.id} />
              <InfoField label="타임스탬프" value={formatDateTime(log.timestamp)} />
              <InfoField label="사용자 ID" value={log.user_id} />
              <InfoField label="세션 ID" value={log.session_id || '-'} />
              <InfoField label="Tool 이름" value={log.tool_name} />
              <InfoField label="실행 시간" value={log.execution_time_ms ? `${log.execution_time_ms}ms` : '-'} />
              <InfoField label="상태" value={log.status} mono={false} />
            </div>
          </section>

          {/* 사용자 쿼리 */}
          {log.user_query && (
            <section>
              <h4 className="text-sm font-medium text-dark-400 mb-3">사용자 쿼리</h4>
              <pre className="bg-dark-900 p-4 rounded-lg text-dark-200 text-sm overflow-x-auto">
                {log.user_query}
              </pre>
            </section>
          )}

          {/* Tool 파라미터 */}
          {log.tool_params && (
            <section>
              <h4 className="text-sm font-medium text-dark-400 mb-3">Tool 파라미터</h4>
              <pre className="bg-dark-900 p-4 rounded-lg text-dark-200 text-sm overflow-x-auto">
                {JSON.stringify(log.tool_params, null, 2)}
              </pre>
            </section>
          )}

          {/* 응답 */}
          {log.response && (
            <section>
              <h4 className="text-sm font-medium text-dark-400 mb-3">응답</h4>
              <pre className="bg-dark-900 p-4 rounded-lg text-dark-200 text-sm overflow-x-auto max-h-96">
                {JSON.stringify(log.response, null, 2)}
              </pre>
            </section>
          )}

          {/* 에러 메시지 */}
          {log.error_message && (
            <section>
              <h4 className="text-sm font-medium text-dark-400 mb-3">에러 메시지</h4>
              <pre className="bg-error/10 border border-error/20 p-4 rounded-lg text-error text-sm overflow-x-auto">
                {log.error_message}
              </pre>
            </section>
          )}
        </div>

        {/* 푸터 */}
        <div className="px-6 py-4 border-t border-dark-700 flex justify-end">
          <Button onClick={onClose} variant="secondary">
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}

function InfoField({
  label,
  value,
  mono = true
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-dark-500 mb-1">{label}</p>
      <p className={`text-dark-200 text-sm ${mono ? 'font-mono' : ''}`}>
        {value}
      </p>
    </div>
  );
}
