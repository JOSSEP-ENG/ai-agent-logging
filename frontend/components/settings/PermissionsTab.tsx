'use client';

import { useState, useEffect } from 'react';
import { Shield, Users, Database, Check, X, Search } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

interface MCPServer {
  id: string;
  name: string;
  transport_type: string;
  status: 'connected' | 'disconnected';
}

interface UserPermission {
  userId: string;
  userName: string;
  userEmail: string;
  role: 'user' | 'auditor' | 'admin';
  hasAccess: boolean;
}

export function PermissionsTab() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<UserPermission[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 임시 데이터 (실제로는 API에서 가져옴)
  useEffect(() => {
    // TODO: API에서 MCP 서버 목록 가져오기
    setServers([
      {
        id: '1',
        name: 'File System Server',
        transport_type: 'stdio',
        status: 'connected',
      },
      {
        id: '2',
        name: 'Database Server',
        transport_type: 'sse',
        status: 'connected',
      },
      {
        id: '3',
        name: 'Web Search Server',
        transport_type: 'stdio',
        status: 'disconnected',
      },
    ]);
  }, []);

  // 선택된 서버의 권한 로드
  useEffect(() => {
    if (selectedServer) {
      loadPermissions(selectedServer);
    }
  }, [selectedServer]);

  const loadPermissions = async (serverId: string) => {
    setIsLoading(true);
    try {
      // TODO: API에서 권한 목록 가져오기
      // 임시 데이터
      setPermissions([
        {
          userId: '1',
          userName: '홍길동',
          userEmail: 'hong@example.com',
          role: 'user',
          hasAccess: true,
        },
        {
          userId: '2',
          userName: '김철수',
          userEmail: 'kim@example.com',
          role: 'user',
          hasAccess: false,
        },
        {
          userId: '3',
          userName: '이영희',
          userEmail: 'lee@example.com',
          role: 'auditor',
          hasAccess: true,
        },
        {
          userId: '4',
          userName: '박민수',
          userEmail: 'park@example.com',
          role: 'admin',
          hasAccess: true,
        },
      ]);
    } catch (error) {
      console.error('Failed to load permissions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePermission = async (userId: string, currentAccess: boolean) => {
    try {
      // TODO: API로 권한 변경 요청
      setPermissions(prev =>
        prev.map(p =>
          p.userId === userId ? { ...p, hasAccess: !currentAccess } : p
        )
      );
    } catch (error) {
      console.error('Failed to toggle permission:', error);
    }
  };

  const filteredPermissions = permissions.filter(
    p =>
      p.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.userEmail.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'auditor':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">권한 관리</h2>
        <p className="text-dark-400">
          MCP 서버별 사용자 접근 권한을 관리합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 서버 목록 */}
        <div className="lg:col-span-1">
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-accent-400" />
              <h3 className="font-semibold text-white">MCP 서버</h3>
            </div>

            <div className="space-y-2">
              {servers.length === 0 ? (
                <p className="text-dark-500 text-sm text-center py-4">
                  등록된 서버가 없습니다.
                </p>
              ) : (
                servers.map(server => (
                  <button
                    key={server.id}
                    onClick={() => setSelectedServer(server.id)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg transition-colors',
                      selectedServer === server.id
                        ? 'bg-accent-500/10 border border-accent-500/30'
                        : 'bg-dark-900 border border-dark-700 hover:border-dark-600'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {server.name}
                        </p>
                        <p className="text-xs text-dark-500 mt-0.5">
                          {server.transport_type}
                        </p>
                      </div>
                      <div
                        className={cn(
                          'w-2 h-2 rounded-full flex-shrink-0 ml-2',
                          server.status === 'connected'
                            ? 'bg-success'
                            : 'bg-dark-600'
                        )}
                      />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 권한 목록 */}
        <div className="lg:col-span-2">
          {!selectedServer ? (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-12 text-center">
              <Shield className="w-12 h-12 text-dark-600 mx-auto mb-4" />
              <p className="text-dark-400">
                권한을 관리할 서버를 선택하세요.
              </p>
            </div>
          ) : (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Users className="w-5 h-5 text-accent-400" />
                <h3 className="font-semibold text-white">사용자 권한</h3>
              </div>

              {/* 검색 */}
              <div className="mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="사용자 검색..."
                    className="w-full pl-10 pr-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white text-sm placeholder-dark-500 focus:outline-none focus:border-accent-500 transition-colors"
                  />
                </div>
              </div>

              {/* 사용자 목록 */}
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              ) : filteredPermissions.length === 0 ? (
                <p className="text-dark-500 text-sm text-center py-8">
                  {searchQuery
                    ? '검색 결과가 없습니다.'
                    : '등록된 사용자가 없습니다.'}
                </p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredPermissions.map(permission => (
                    <div
                      key={permission.userId}
                      className="flex items-center justify-between p-3 bg-dark-900 border border-dark-700 rounded-lg hover:border-dark-600 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-medium text-white">
                            {permission.userName}
                          </p>
                          <span
                            className={cn(
                              'px-2 py-0.5 text-xs font-medium border rounded',
                              getRoleBadgeColor(permission.role)
                            )}
                          >
                            {permission.role}
                          </span>
                        </div>
                        <p className="text-xs text-dark-500 truncate">
                          {permission.userEmail}
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          togglePermission(
                            permission.userId,
                            permission.hasAccess
                          )
                        }
                        className={cn(
                          'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ml-4',
                          permission.hasAccess
                            ? 'bg-success/10 text-success border border-success/30 hover:bg-success/20'
                            : 'bg-dark-800 text-dark-400 border border-dark-700 hover:bg-dark-700'
                        )}
                      >
                        {permission.hasAccess ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            접근 허용
                          </>
                        ) : (
                          <>
                            <X className="w-3.5 h-3.5" />
                            접근 거부
                          </>
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* 안내 메시지 */}
              <div className="mt-4 p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                <p className="text-xs text-blue-400">
                  <strong>안내:</strong> 관리자(admin)는 모든 MCP 서버에 자동으로
                  접근 권한이 부여됩니다.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
