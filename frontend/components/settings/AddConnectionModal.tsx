'use client';

import { useState } from 'react';
import { X, Database, Cloud } from 'lucide-react';
import { mcpApi } from '@/lib/api';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

type TabType = 'external' | 'custom';

export function AddConnectionModal({ onClose, onSuccess }: Props) {
  const [activeTab, setActiveTab] = useState<TabType>('external');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [host, setHost] = useState('localhost');
  const [port, setPort] = useState('3306');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [database, setDatabase] = useState('');
  const [readOnly, setReadOnly] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTest = async () => {
    setIsLoading(true);
    setError('');

    try {
      const connection = await mcpApi.createConnection(
        name,
        'mysql',
        { host, port: parseInt(port), database, read_only: readOnly },
        { username, password }
      );

      const testResult = await mcpApi.testConnection(connection.id);

      if (testResult.success) {
        onSuccess();
      } else {
        setError(testResult.error || '연결 테스트 실패');
      }
    } catch (err: any) {
      setError(err.message || '연결 생성 실패');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/80" onClick={onClose} />

      <div className="relative bg-dark-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">MCP 서버 연결 추가</h2>
            <button
              onClick={onClose}
              className="text-dark-400 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* 탭 메뉴 */}
          <div className="flex gap-2 mb-6 border-b border-dark-700">
            <button
              onClick={() => setActiveTab('external')}
              className={`
                flex items-center gap-2 px-4 py-3 border-b-2 transition-colors
                ${
                  activeTab === 'external'
                    ? 'border-accent-500 text-accent-400'
                    : 'border-transparent text-dark-400 hover:text-dark-200'
                }
              `}
            >
              <Cloud className="w-5 h-5" />
              <span className="font-medium">외부 MCP 서버</span>
            </button>

            <button
              onClick={() => setActiveTab('custom')}
              className={`
                flex items-center gap-2 px-4 py-3 border-b-2 transition-colors
                ${
                  activeTab === 'custom'
                    ? 'border-accent-500 text-accent-400'
                    : 'border-transparent text-dark-400 hover:text-dark-200'
                }
              `}
            >
              <Database className="w-5 h-5" />
              <span className="font-medium">커스텀 MCP 서버</span>
            </button>
          </div>

          {/* 외부 MCP 서버 탭 */}
          {activeTab === 'external' && (
            <div className="space-y-4">
              <p className="text-dark-400 mb-4">
                OAuth 인증을 통해 외부 서비스에 연결합니다
              </p>

              <button
                disabled
                className="w-full p-4 border border-dark-700 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <h3 className="text-white font-semibold">Notion (준비 중)</h3>
                <p className="text-dark-400 text-sm mt-1">
                  Notion 워크스페이스의 페이지와 데이터베이스를 조회합니다
                </p>
              </button>

              <button
                disabled
                className="w-full p-4 border border-dark-700 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <h3 className="text-white font-semibold">
                  Google Calendar (준비 중)
                </h3>
                <p className="text-dark-400 text-sm mt-1">
                  Google 캘린더 일정을 조회합니다
                </p>
              </button>

              <button
                disabled
                className="w-full p-4 border border-dark-700 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <h3 className="text-white font-semibold">
                  Google Drive (준비 중)
                </h3>
                <p className="text-dark-400 text-sm mt-1">
                  Google 드라이브 파일을 검색하고 읽습니다
                </p>
              </button>
            </div>
          )}

          {/* 커스텀 MCP 서버 탭 */}
          {activeTab === 'custom' && (
            <div className="space-y-4">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-2">
                  MySQL 데이터베이스 연결
                </h3>
                <p className="text-dark-400 text-sm">
                  MySQL 서버에 직접 연결하여 데이터를 조회합니다
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  연결 이름 *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="예: Production DB"
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  설명 (선택)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="예: 운영 서버 고객 데이터베이스"
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    호스트 *
                  </label>
                  <input
                    type="text"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="localhost"
                    className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    포트 *
                  </label>
                  <input
                    type="number"
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    placeholder="3306"
                    className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  사용자명 *
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="root"
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  비밀번호 *
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  데이터베이스 *
                </label>
                <input
                  type="text"
                  value={database}
                  onChange={(e) => setDatabase(e.target.value)}
                  placeholder="mydb"
                  className="w-full px-4 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white placeholder-dark-500 focus:outline-none focus:border-accent-500"
                  required
                />
              </div>

              <label className="flex items-center gap-2 text-dark-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={readOnly}
                  onChange={(e) => setReadOnly(e.target.checked)}
                  className="rounded bg-dark-900 border-dark-700 text-accent-500 focus:ring-accent-500"
                />
                읽기 전용 모드 (권장)
              </label>

              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div className="flex justify-end pt-4">
                <button
                  onClick={handleTest}
                  disabled={
                    isLoading ||
                    !name ||
                    !username ||
                    !password ||
                    !database
                  }
                  className="px-6 py-2 bg-accent-500 hover:bg-accent-600 disabled:bg-dark-700 disabled:text-dark-500 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                >
                  {isLoading ? '테스트 중...' : '테스트 및 저장'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
