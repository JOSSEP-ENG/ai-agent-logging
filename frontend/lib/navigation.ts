/**
 * 네비게이션 설정
 * 
 * 메뉴 항목과 페이지 설정을 중앙에서 관리합니다.
 */

import { 
  MessageSquare, 
  Database, 
  LayoutDashboard, 
  FileText,
  User,
  Bell,
  Shield,
  Settings,
} from 'lucide-react';
import type { User as UserType } from './api';

// ============ 타입 정의 ============

export type UserRole = 'user' | 'auditor' | 'admin';

export interface MenuItem {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  href: string;
  roles: UserRole[];
  separator?: boolean;
  badge?: () => number | string;
}

export interface TabConfig {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  componentPath: string;  // 컴포넌트 경로 (동적 import용)
  roles?: UserRole[];
}

export interface PageConfig {
  title: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: UserRole[];
  tabs?: TabConfig[];
  showBackButton?: boolean;
}

// ============ 전역 메뉴 ============

export const GLOBAL_MENU: MenuItem[] = [
  {
    id: 'chat',
    icon: MessageSquare,
    label: '채팅',
    href: '/chat/history',
    roles: ['user', 'auditor', 'admin'],
  },
  {
    id: 'settings',
    icon: Database,
    label: 'MCP 서버',
    href: '/settings',
    roles: ['user', 'auditor', 'admin'],
  },
  {
    id: 'admin',
    icon: LayoutDashboard,
    label: '시스템 현황 모니터링',
    href: '/admin',
    roles: ['admin'],
    separator: true,
  },
  {
    id: 'audit-logs',
    icon: FileText,
    label: '로그 조회',
    href: '/audit-logs',
    roles: ['auditor', 'admin'],
  },
];

// ============ 페이지 설정 ============

export const PAGE_CONFIGS: Record<string, PageConfig> = {
  '/settings': {
    title: 'MCP 서버',
    description: 'MCP 서버 연결 및 권한 관리',
    icon: Database,
    roles: ['user', 'auditor', 'admin'],
    tabs: [
      {
        id: 'connections',
        label: '연결 관리',
        icon: Database,
        componentPath: '@/components/settings/MCPConnectionsTab',
      },
      {
        id: 'permissions',
        label: '권한 관리',
        icon: Shield,
        componentPath: '@/components/settings/PermissionsTab',
      },
    ],
  },
  '/admin': {
    title: '시스템 현황 모니터링',
    description: '시스템 상태 및 성능 모니터링',
    icon: LayoutDashboard,
    roles: ['admin'],
  },
  '/audit-logs': {
    title: '로그 조회',
    description: '시스템 감사 로그 조회 및 분석',
    icon: FileText,
    roles: ['auditor', 'admin'],
  },
  '/profile': {
    title: '프로필',
    description: '내 정보 및 개인 설정 관리',
    icon: User,
    roles: ['user', 'auditor', 'admin'],
    tabs: [
      {
        id: 'info',
        label: '프로필 정보',
        icon: User,
        componentPath: '@/components/profile/ProfileInfoTab',
      },
      {
        id: 'notifications',
        label: '알림 설정',
        icon: Bell,
        componentPath: '@/components/profile/NotificationsTab',
      },
      {
        id: 'security',
        label: '보안 설정',
        icon: Shield,
        componentPath: '@/components/profile/SecurityTab',
      },
      {
        id: 'password',
        label: '비밀번호 변경',
        icon: Shield,
        componentPath: '@/components/profile/PasswordChangeTab',
      },
    ],
  },
  '/preferences': {
    title: '환경 설정',
    description: '시스템 환경 및 기본 설정 관리',
    icon: Settings,
    roles: ['user', 'auditor', 'admin'],
    tabs: [
      {
        id: 'general',
        label: '일반 설정',
        icon: Settings,
        componentPath: '@/components/preferences/GeneralTab',
      },
      {
        id: 'appearance',
        label: '테마 및 표시',
        icon: Settings,
        componentPath: '@/components/preferences/AppearanceTab',
      },
      {
        id: 'language',
        label: '언어 및 지역',
        icon: Settings,
        componentPath: '@/components/preferences/LanguageTab',
      },
    ],
  },
};

// ============ 유틸리티 함수 ============

/**
 * 사용자 역할에 따라 메뉴 필터링
 */
export function filterMenuByRole(menu: MenuItem[], userRole: UserRole): MenuItem[] {
  return menu.filter(item => item.roles.includes(userRole));
}

/**
 * 페이지 접근 권한 확인
 */
export function hasPageAccess(pageKey: string, userRole: UserRole): boolean {
  const config = PAGE_CONFIGS[pageKey];
  return config ? config.roles.includes(userRole) : false;
}

/**
 * 사용자 역할에 따라 탭 필터링
 */
export function filterTabsByRole(tabs: TabConfig[], userRole: UserRole): TabConfig[] {
  return tabs.filter(tab => !tab.roles || tab.roles.includes(userRole));
}
