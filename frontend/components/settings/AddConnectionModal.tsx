'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { mcpApi } from '@/lib/api';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

export function AddConnectionModal({ onClose, onSuccess }: Props) {
  const [step, setStep] = useState<'type' | 'config' | 'test'>('type');
  const [type, setType] = useState<string>('');
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
        type,
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

      <div className="relative bg-dark-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">연결 추가</h2>
            <button
              onClick={onClose}
              className="text-dark-400 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {step === 'type' && (
            <div className="space-y-4">
              <p className="text-dark-400">연결 타입을 선택하세요:</p>

              <button
                onClick={() => {
                  setType('mysql');
                  setStep('config');
                }}
                className="w-full p-4 border border-dark-700 rounded-lg hover:bg-dark-700 hover:border-accent-500 transition-colors text-left"
              >
                <h3 className="text-white font-semibold">MySQL 데이터베이스</h3>
                <p className="text-dark-400 text-sm mt-1">
                  MySQL 서버에 연결합니다
                </p>
              </button>

              <button
                disabled
                className="w-full p-4 border border-dark-700 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <h3 className="text-white font-semibold">
                  Notion (준비 중)
                </h3>
                <p className="text-dark-400 text-sm mt-1">OAuth 인증</p>
              </button>

              <button
                disabled
                className="w-full p-4 border border-dark-700 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <h3 className="text-white font-semibold">
                  Google Calendar (준비 중)
                </h3>
                <p className="text-dark-400 text-sm mt-1">OAuth 인증</p>
              </button>
            </div>
          )}

          {step === 'config' && type === 'mysql' && (
            <div className="space-y-4">
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

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep('type')}
                  className="px-4 py-2 text-dark-300 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
                >
                  뒤로
                </button>

                <button
                  onClick={handleTest}
                  disabled={
                    isLoading ||
                    !name ||
                    !username ||
                    !password ||
                    !database
                  }
                  className="flex-1 px-4 py-2 bg-accent-500 hover:bg-accent-600 disabled:bg-dark-700 disabled:text-dark-500 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
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
