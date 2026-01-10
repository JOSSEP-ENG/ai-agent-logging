'use client';

import { useState, useEffect } from 'react';
import { FileText, RefreshCw, Download } from 'lucide-react';
import { Button } from '@/components/ui';
import { adminApi } from '@/lib/api';
import { AuditLogFilters, FilterState } from './AuditLogFilters';
import { AuditLogTable } from './AuditLogTable';
import { AuditLogDetail } from './AuditLogDetail';

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

export function AuditLogsTab() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 페이지네이션 상태
  const [page, setPage] = useState(1);
  const [limit] = useState(50);

  // 필터 상태
  const [filters, setFilters] = useState<FilterState>({
    user_id: '',
    tool_name: '',
    status: '',
    start_date: '',
    end_date: '',
  });

  // 상세 모달 상태
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    loadLogs();
  }, [page, filters]);

  const loadLogs = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const offset = (page - 1) * limit;
      const response = await adminApi.getAuditLogs({
        limit,
        offset,
        user_id: filters.user_id || undefined,
        tool_name: filters.tool_name || undefined,
        status: filters.status || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      });

      setLogs(response.logs);
      setTotal(response.total);
    } catch (err: any) {
      console.error('Failed to load audit logs:', err);
      setError(err.detail || '로그를 불러올 수 없습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    setPage(1); // 필터 변경 시 첫 페이지로
  };

  const handleExport = async () => {
    // CSV 내보내기 기능 (향후 구현)
    alert('CSV 내보내기 기능 (향후 구현)');
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">감사 로그 조회</h2>
          <p className="text-dark-400 mt-1">시스템 Tool 호출 기록 조회</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleExport} variant="secondary" size="sm">
            <Download className="w-4 h-4" />
            내보내기
          </Button>
          <Button onClick={loadLogs} variant="ghost" size="sm">
            <RefreshCw className="w-4 h-4" />
            새로고침
          </Button>
        </div>
      </div>

      {/* 필터 */}
      <AuditLogFilters
        filters={filters}
        onChange={handleFilterChange}
      />

      {/* 결과 요약 */}
      <div className="flex items-center justify-between text-sm text-dark-400">
        <span>총 {total}건의 로그</span>
        <span>
          페이지 {page} / {totalPages || 1}
        </span>
      </div>

      {/* 테이블 */}
      {error ? (
        <div className="text-center py-12 text-error">{error}</div>
      ) : (
        <AuditLogTable
          logs={logs}
          isLoading={isLoading}
          onRowClick={setSelectedLog}
        />
      )}

      {/* 페이지네이션 */}
      {total > 0 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            variant="secondary"
            size="sm"
          >
            이전
          </Button>
          <span className="text-dark-300 px-4">
            {page} / {totalPages}
          </span>
          <Button
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
            variant="secondary"
            size="sm"
          >
            다음
          </Button>
        </div>
      )}

      {/* 상세 모달 */}
      {selectedLog && (
        <AuditLogDetail
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
}
