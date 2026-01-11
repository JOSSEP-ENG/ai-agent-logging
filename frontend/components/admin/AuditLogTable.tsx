'use client';

import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email?: string;
  user_name?: string;
  tool_name: string;
  status: 'success' | 'fail' | 'denied';
  execution_time_ms?: string;
}

interface Props {
  logs: AuditLog[];
  isLoading: boolean;
  onRowClick: (log: AuditLog) => void;
}

export function AuditLogTable({ logs, isLoading, onRowClick }: Props) {
  if (isLoading) {
    return (
      <div className="text-center py-12 text-dark-400">
        로그를 불러오는 중...
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-12 text-dark-400">
        조회된 로그가 없습니다.
      </div>
    );
  }

  return (
    <div className="bg-dark-800 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-dark-700">
            <tr>
              <th className="text-left py-3 px-4 text-dark-300 font-medium">
                시간
              </th>
              <th className="text-left py-3 px-4 text-dark-300 font-medium">
                사용자
              </th>
              <th className="text-left py-3 px-4 text-dark-300 font-medium">
                Tool
              </th>
              <th className="text-left py-3 px-4 text-dark-300 font-medium">
                상태
              </th>
              <th className="text-right py-3 px-4 text-dark-300 font-medium">
                실행 시간
              </th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr
                key={log.id}
                onClick={() => onRowClick(log)}
                className="border-t border-dark-700 hover:bg-dark-700/50 cursor-pointer transition-colors"
              >
                <td className="py-3 px-4 text-dark-200">
                  {formatDateTime(log.timestamp)}
                </td>
                <td className="py-3 px-4 text-dark-200">
                  {log.user_email ? (
                    <div>
                      <div className="font-medium">{log.user_email}</div>
                      {log.user_name && (
                        <div className="text-xs text-dark-400 mt-0.5">
                          {log.user_name}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-dark-400 font-mono text-sm">
                      {log.user_id}
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 text-dark-200 font-mono text-sm">
                  {log.tool_name}
                </td>
                <td className="py-3 px-4">
                  <StatusBadge status={log.status} />
                </td>
                <td className="py-3 px-4 text-right text-dark-300 font-mono text-sm">
                  {log.execution_time_ms ? `${log.execution_time_ms}ms` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: 'success' | 'fail' | 'denied' }) {
  const config = {
    success: {
      icon: CheckCircle2,
      label: '성공',
      className: 'bg-success/10 text-success',
    },
    fail: {
      icon: XCircle,
      label: '실패',
      className: 'bg-error/10 text-error',
    },
    denied: {
      icon: AlertCircle,
      label: '거부',
      className: 'bg-warning/10 text-warning',
    },
  };

  const { icon: Icon, label, className } = config[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${className}`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </span>
  );
}
