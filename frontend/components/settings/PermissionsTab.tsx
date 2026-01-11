'use client';

import { useState, useEffect } from 'react';
import { Shield, Users, Database, Check, X, Search, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import { adminApi, mcpApi, type MCPConnection, type ToolPermission, type ConnectionTools } from '@/lib/api';

interface UserPermission {
  userId: string;
  userName: string;
  userEmail: string;
  role: 'user' | 'auditor' | 'admin';
}

export function PermissionsTab() {
  const [servers, setServers] = useState<MCPConnection[]>([]);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [users, setUsers] = useState<UserPermission[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Tool 권한 관리
  const [connectionTools, setConnectionTools] = useState<string[]>([]);
  const [userPermissions, setUserPermissions] = useState<ToolPermission[]>([]);
  const [expandedTools, setExpandedTools] = useState(false);

  // MCP 서버 목록 로드
  useEffect(() => {
    loadServers();
    loadUsers();
  }, []);

  // 선택된 서버와 사용자의 권한 로드
  useEffect(() => {
    if (selectedServer && selectedUser) {
      loadToolsAndPermissions();
    }
  }, [selectedServer, selectedUser]);

  const loadServers = async () => {
    try {
      const connections = await mcpApi.getUserConnections();
      setServers(connections);
    } catch (error) {
      console.error('Failed to load servers:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await adminApi.getUsers();
      setUsers(
        response.users.map(u => ({
          userId: u.id,
          userName: u.name,
          userEmail: u.email,
          role: u.role,
        }))
      );
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const loadToolsAndPermissions = async () => {
    if (!selectedServer || !selectedUser) return;

    setIsLoading(true);
    try {
      // Tool 목록 조회
      const toolsData = await adminApi.getConnectionTools(selectedServer);
      setConnectionTools(toolsData.tools);

      // 사용자 권한 조회
      const permissions = await adminApi.getUserToolPermissions(
        selectedUser,
        selectedServer
      );
      setUserPermissions(permissions);
    } catch (error) {
      console.error('Failed to load tools and permissions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPermissionForTool = (toolName: string): 'allowed' | 'blocked' | null => {
    const permission = userPermissions.find(
      p => p.connection_id === selectedServer && p.tool_name === toolName
    );

    if (!permission) return null; // 설정되지 않음 (기본: 허용)
    return permission.permission_type as 'allowed' | 'blocked';
  };

  const toggleToolPermission = async (toolName: string) => {
    if (!selectedServer || !selectedUser) return;

    const currentPermission = getPermissionForTool(toolName);
    const newPermission: 'allowed' | 'blocked' =
      currentPermission === 'blocked' ? 'allowed' : 'blocked';

    try {
      await adminApi.setToolPermission(selectedUser, {
        connection_id: selectedServer,
        tool_name: toolName,
        permission_type: newPermission,
      });

      // 권한 목록 새로고침
      await loadToolsAndPermissions();
    } catch (error) {
      console.error('Failed to toggle permission:', error);
    }
  };

  const filteredUsers = users.filter(
    u =>
      u.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.userEmail.toLowerCase().includes(searchQuery.toLowerCase())
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

  const selectedUserData = users.find(u => u.userId === selectedUser);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Tool 권한 관리</h2>
        <p className="text-dark-400">
          사용자별 MCP Tool 접근 권한을 세부적으로 관리합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* MCP 서버 목록 */}
        <div className="lg:col-span-3">
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
                          {server.type}
                        </p>
                      </div>
                      <div
                        className={cn(
                          'w-2 h-2 rounded-full flex-shrink-0 ml-2',
                          server.is_active ? 'bg-success' : 'bg-dark-600'
                        )}
                      />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 사용자 목록 */}
        <div className="lg:col-span-3">
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-5 h-5 text-accent-400" />
              <h3 className="font-semibold text-white">사용자</h3>
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
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredUsers.map(user => (
                <button
                  key={user.userId}
                  onClick={() => setSelectedUser(user.userId)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    selectedUser === user.userId
                      ? 'bg-accent-500/10 border border-accent-500/30'
                      : 'bg-dark-900 border border-dark-700 hover:border-dark-600'
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-white truncate flex-1">
                      {user.userName}
                    </p>
                    <span
                      className={cn(
                        'px-2 py-0.5 text-xs font-medium border rounded',
                        getRoleBadgeColor(user.role)
                      )}
                    >
                      {user.role}
                    </span>
                  </div>
                  <p className="text-xs text-dark-500 truncate">{user.userEmail}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tool 권한 상세 */}
        <div className="lg:col-span-6">
          {!selectedServer || !selectedUser ? (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-12 text-center">
              <Shield className="w-12 h-12 text-dark-600 mx-auto mb-4" />
              <p className="text-dark-400">
                MCP 서버와 사용자를 선택하여 Tool 권한을 관리하세요.
              </p>
            </div>
          ) : (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-white">Tool 권한</h3>
                  {selectedUserData && (
                    <p className="text-sm text-dark-400 mt-1">
                      {selectedUserData.userName} ({selectedUserData.userEmail})
                    </p>
                  )}
                </div>
                <button
                  onClick={() => setExpandedTools(!expandedTools)}
                  className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                >
                  {expandedTools ? (
                    <ChevronDown className="w-4 h-4 text-dark-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-dark-400" />
                  )}
                </button>
              </div>

              {/* Tool 목록 */}
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              ) : connectionTools.length === 0 ? (
                <p className="text-dark-500 text-sm text-center py-8">
                  이 서버에는 사용 가능한 Tool이 없습니다.
                </p>
              ) : (
                <div className="space-y-2">
                  {connectionTools.map(toolName => {
                    const permission = getPermissionForTool(toolName);
                    const isBlocked = permission === 'blocked';
                    const isExplicitlyAllowed = permission === 'allowed';

                    return (
                      <div
                        key={toolName}
                        className="flex items-center justify-between p-3 bg-dark-900 border border-dark-700 rounded-lg hover:border-dark-600 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">{toolName}</p>
                          <p className="text-xs text-dark-500 mt-0.5">
                            {isBlocked
                              ? '접근이 차단되었습니다'
                              : isExplicitlyAllowed
                              ? '접근이 명시적으로 허용되었습니다'
                              : '기본 허용 (권한 설정 없음)'}
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => toggleToolPermission(toolName)}
                            className={cn(
                              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                              isBlocked
                                ? 'bg-dark-800 text-dark-400 border border-dark-700 hover:bg-dark-700'
                                : 'bg-success/10 text-success border border-success/30 hover:bg-success/20'
                            )}
                          >
                            {isBlocked ? (
                              <>
                                <X className="w-3.5 h-3.5" />
                                차단됨
                              </>
                            ) : (
                              <>
                                <Check className="w-3.5 h-3.5" />
                                허용됨
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 안내 메시지 */}
              <div className="mt-4 p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                <p className="text-xs text-blue-400">
                  <strong>안내:</strong> 관리자(admin)는 모든 Tool에 자동으로 접근
                  권한이 부여됩니다. 권한이 명시적으로 설정되지 않은 Tool은 기본적으로
                  허용됩니다.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
