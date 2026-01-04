'use client';

import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { mcpApi, MCPConnection } from '@/lib/api';
import { ConnectionList } from './ConnectionList';
import { AddConnectionModal } from './AddConnectionModal';

export function MCPConnectionsTab() {
  const [connections, setConnections] = useState<MCPConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const loadConnections = async () => {
    try {
      const data = await mcpApi.getUserConnections();
      setConnections(data);
    } catch (error) {
      console.error('Failed to load connections:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('이 연결을 삭제하시겠습니까?')) return;

    try {
      await mcpApi.deleteConnection(id);
      setConnections(connections.filter((c) => c.id !== id));
    } catch (error) {
      console.error('Failed to delete connection:', error);
      alert('연결 삭제에 실패했습니다');
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await mcpApi.testConnection(id);
      if (result.success) {
        alert(`연결 성공! ${result.tools_count}개의 도구를 사용할 수 있습니다.`);
      } else {
        alert(`연결 실패: ${result.error}`);
      }
      loadConnections(); // 테스트 상태 업데이트 반영
    } catch (error) {
      console.error('Failed to test connection:', error);
      alert('연결 테스트에 실패했습니다');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-white">데이터 소스</h2>
          <p className="text-dark-400 mt-1">데이터베이스 및 서비스 연결 관리</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-accent-500 hover:bg-accent-600 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          연결 추가
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-dark-400">로딩 중...</div>
      ) : (
        <ConnectionList
          connections={connections}
          onDelete={handleDelete}
          onTest={handleTest}
        />
      )}

      {showAddModal && (
        <AddConnectionModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadConnections();
          }}
        />
      )}
    </div>
  );
}
