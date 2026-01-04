import { Database, Trash2, TestTube, CheckCircle, XCircle } from 'lucide-react';
import { MCPConnection } from '@/lib/api';

interface Props {
  connections: MCPConnection[];
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}일 전`;

  return date.toLocaleDateString('ko-KR');
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    mysql: 'MySQL 데이터베이스',
    notion: 'Notion',
    google_calendar: 'Google Calendar',
  };
  return labels[type] || type;
}

export function ConnectionList({ connections, onDelete, onTest }: Props) {
  if (connections.length === 0) {
    return (
      <div className="p-12 text-center bg-dark-800 rounded-lg border border-dark-700">
        <Database className="w-12 h-12 mx-auto mb-4 text-dark-500" />
        <p className="text-dark-400">아직 연결된 데이터 소스가 없습니다</p>
        <p className="text-dark-500 text-sm mt-2">
          첫 번째 데이터 소스를 추가해보세요
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {connections.map((conn) => (
        <div
          key={conn.id}
          className="p-6 bg-dark-800 rounded-lg border border-dark-700 hover:border-dark-600 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-accent-500/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Database className="w-6 h-6 text-accent-500" />
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white">
                  {conn.name}
                </h3>
                <p className="text-dark-400 text-sm mt-1">
                  {getTypeLabel(conn.type)}
                </p>

                {conn.last_tested_at && (
                  <div className="flex items-center gap-2 mt-2">
                    {conn.last_test_status === 'success' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-xs text-dark-500">
                      마지막 테스트: {formatDate(conn.last_tested_at)} -{' '}
                      {conn.last_test_status === 'success'
                        ? '성공'
                        : '실패'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => onTest(conn.id)}
                className="px-3 py-2 text-sm text-dark-300 hover:text-white hover:bg-dark-700 rounded-lg transition-colors flex items-center gap-2"
                title="연결 테스트"
              >
                <TestTube className="w-4 h-4" />
                테스트
              </button>

              <button
                onClick={() => onDelete(conn.id)}
                className="px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-dark-700 rounded-lg transition-colors"
                title="삭제"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
