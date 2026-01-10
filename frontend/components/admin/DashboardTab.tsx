'use client';

import { useState, useEffect } from 'react';
import {
  Users,
  MessageSquare,
  Database,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import { adminApi, DashboardStats } from '@/lib/api';
import { formatNumber, getRoleName } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function DashboardTab() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [dailyStats, setDailyStats] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [dashboardData, dailyData] = await Promise.all([
        adminApi.getDashboard(),
        adminApi.getDailyStats(7),
      ]);

      setStats(dashboardData);
      setDailyStats(dailyData);
    } catch (err: any) {
      console.error('Dashboard load error:', err);
      setError(err.detail || '대시보드를 불러올 수 없습니다. Admin 권한이 필요합니다.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="loading-dots mb-4">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <p className="text-dark-400">대시보드 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-error/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-error" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">접근할 수 없습니다</h2>
        <p className="text-dark-400 mb-6">{error}</p>
        <Button onClick={loadDashboard}>다시 시도</Button>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">대시보드</h2>
          <p className="text-dark-400 mt-1">시스템 현황 모니터링</p>
        </div>
        <Button onClick={loadDashboard} variant="ghost" size="sm">
          <RefreshCw className="w-4 h-4" />
          새로고침
        </Button>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="전체 사용자"
          value={formatNumber(stats.users.total)}
          subValue={`활성 ${stats.users.active}명`}
          icon={Users}
          trend={`최근 7일 +${stats.users.new_last_7_days}`}
          color="accent"
        />
        <StatCard
          title="대화 세션"
          value={formatNumber(stats.sessions.total)}
          subValue={`오늘 ${stats.sessions.today_sessions}개`}
          icon={MessageSquare}
          trend={`총 메시지 ${formatNumber(stats.sessions.total_messages)}`}
          color="success"
        />
        <StatCard
          title="감사 로그"
          value={formatNumber(stats.audit.total)}
          subValue={`오늘 ${stats.audit.today_logs}건`}
          icon={Activity}
          trend={`성공률 ${stats.audit.success_rate}%`}
          color="warning"
        />
        <StatCard
          title="시스템 상태"
          value={stats.system.status === 'healthy' ? '정상' : '점검필요'}
          subValue={`DB: ${stats.system.database}`}
          icon={Database}
          color={stats.system.status === 'healthy' ? 'success' : 'error'}
        />
      </div>

      {/* 상세 통계 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 역할별 사용자 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-accent-400" />
              역할별 사용자
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.users.by_role).map(([role, count]) => (
                <div key={role} className="flex items-center justify-between">
                  <span className="text-dark-300">{getRoleName(role)}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-dark-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent-500 rounded-full"
                        style={{ width: `${(count / stats.users.total) * 100}%` }}
                      />
                    </div>
                    <span className="text-dark-200 font-medium w-12 text-right">
                      {count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 상태별 감사 로그 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-accent-400" />
              감사 로그 상태
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.audit.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {status === 'success' && <CheckCircle2 className="w-4 h-4 text-success" />}
                    {status === 'fail' && <XCircle className="w-4 h-4 text-error" />}
                    {status === 'denied' && <AlertCircle className="w-4 h-4 text-warning" />}
                    {status === 'pending' && <Clock className="w-4 h-4 text-dark-400" />}
                    <span className="text-dark-300 capitalize">{status}</span>
                  </div>
                  <span className="text-dark-200 font-medium">
                    {formatNumber(count)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Tools */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5 text-accent-400" />
            자주 사용되는 Tool
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats.audit.top_tools.length === 0 ? (
            <p className="text-dark-500 text-center py-4">아직 Tool 사용 기록이 없습니다</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stats.audit.top_tools.map((tool, index) => (
                <div
                  key={tool.tool}
                  className="flex items-center gap-3 p-3 bg-dark-700/50 rounded-lg"
                >
                  <div className={cn(
                    'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold',
                    index === 0 && 'bg-accent-500 text-white',
                    index === 1 && 'bg-dark-600 text-dark-200',
                    index > 1 && 'bg-dark-700 text-dark-400'
                  )}>
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-dark-200 font-mono text-sm truncate">
                      {tool.tool}
                    </p>
                    <p className="text-xs text-dark-500">
                      {formatNumber(tool.count)}회 호출
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 일별 통계 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-accent-400" />
            최근 7일 활동
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-3 px-4 text-dark-400 font-medium">날짜</th>
                  <th className="text-right py-3 px-4 text-dark-400 font-medium">감사 로그</th>
                  <th className="text-right py-3 px-4 text-dark-400 font-medium">세션</th>
                  <th className="text-right py-3 px-4 text-dark-400 font-medium">신규 가입</th>
                </tr>
              </thead>
              <tbody>
                {dailyStats.map((day) => (
                  <tr key={day.date} className="border-b border-dark-800 hover:bg-dark-800/50">
                    <td className="py-3 px-4 text-dark-200">{day.date}</td>
                    <td className="py-3 px-4 text-right text-dark-300">{day.audit_logs}</td>
                    <td className="py-3 px-4 text-right text-dark-300">{day.sessions}</td>
                    <td className="py-3 px-4 text-right text-dark-300">{day.new_users}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============ 서브 컴포넌트 ============

interface StatCardProps {
  title: string;
  value: string;
  subValue?: string;
  icon: any;
  trend?: string;
  color?: 'accent' | 'success' | 'warning' | 'error';
}

function StatCard({ title, value, subValue, icon: Icon, trend, color = 'accent' }: StatCardProps) {
  const colors = {
    accent: 'bg-accent-500/10 text-accent-400',
    success: 'bg-success/10 text-success',
    warning: 'bg-warning/10 text-warning',
    error: 'bg-error/10 text-error',
  };

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-dark-400 text-sm mb-1">{title}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
            {subValue && (
              <p className="text-sm text-dark-400 mt-1">{subValue}</p>
            )}
          </div>
          <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', colors[color])}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        {trend && (
          <p className="text-xs text-dark-500 mt-3 pt-3 border-t border-dark-700">
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
