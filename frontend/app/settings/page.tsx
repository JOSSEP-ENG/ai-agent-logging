'use client';

import { MCPConnectionsTab } from '@/components/settings/MCPConnectionsTab';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-dark-900">
      <div className="max-w-6xl mx-auto p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">설정</h1>
          <p className="text-dark-400">MCP 연결 및 설정 관리</p>
        </div>

        <MCPConnectionsTab />
      </div>
    </div>
  );
}
