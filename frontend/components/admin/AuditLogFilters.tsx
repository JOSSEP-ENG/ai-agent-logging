'use client';

import { useState } from 'react';
import { Input, Button } from '@/components/ui';
import { Search, X } from 'lucide-react';

export interface FilterState {
  user_id: string;
  tool_name: string;
  status: string;
  start_date: string;
  end_date: string;
}

interface Props {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}

export function AuditLogFilters({ filters, onChange }: Props) {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters);

  const handleApply = () => {
    onChange(localFilters);
  };

  const handleReset = () => {
    const resetFilters: FilterState = {
      user_id: '',
      tool_name: '',
      status: '',
      start_date: '',
      end_date: '',
    };
    setLocalFilters(resetFilters);
    onChange(resetFilters);
  };

  return (
    <div className="bg-dark-800 rounded-lg p-6 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 사용자 ID */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            사용자 ID
          </label>
          <Input
            value={localFilters.user_id}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, user_id: e.target.value })
            }
            placeholder="user@example.com"
          />
        </div>

        {/* Tool 이름 */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Tool 이름
          </label>
          <Input
            value={localFilters.tool_name}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, tool_name: e.target.value })
            }
            placeholder="mcp_tool_name"
          />
        </div>

        {/* 상태 */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            상태
          </label>
          <select
            value={localFilters.status}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, status: e.target.value })
            }
            className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-accent-500"
          >
            <option value="">전체</option>
            <option value="success">성공</option>
            <option value="fail">실패</option>
            <option value="denied">거부</option>
          </select>
        </div>

        {/* 시작 날짜 */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            시작 날짜
          </label>
          <Input
            type="date"
            value={localFilters.start_date}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, start_date: e.target.value })
            }
          />
        </div>

        {/* 종료 날짜 */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            종료 날짜
          </label>
          <Input
            type="date"
            value={localFilters.end_date}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, end_date: e.target.value })
            }
          />
        </div>
      </div>

      {/* 버튼 */}
      <div className="flex gap-2 justify-end">
        <Button onClick={handleReset} variant="ghost" size="sm">
          <X className="w-4 h-4" />
          초기화
        </Button>
        <Button onClick={handleApply} size="sm">
          <Search className="w-4 h-4" />
          검색
        </Button>
      </div>
    </div>
  );
}
