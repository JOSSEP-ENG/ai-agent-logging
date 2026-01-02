/**
 * 유틸리티 함수
 */
import { clsx, type ClassValue } from 'clsx';

/**
 * 클래스 이름 결합
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * 날짜 포맷팅
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  // 1분 이내
  if (diff < 60 * 1000) {
    return '방금 전';
  }
  
  // 1시간 이내
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000));
    return `${minutes}분 전`;
  }
  
  // 24시간 이내
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours}시간 전`;
  }
  
  // 7일 이내
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000));
    return `${days}일 전`;
  }
  
  // 그 외
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * 날짜/시간 포맷팅
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 숫자 포맷팅 (천 단위 구분)
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('ko-KR');
}

/**
 * 역할 이름 (한글)
 */
export function getRoleName(role: string): string {
  const roleNames: Record<string, string> = {
    user: '사용자',
    auditor: '감사자',
    admin: '관리자',
  };
  return roleNames[role] || role;
}

/**
 * 역할 색상
 */
export function getRoleColor(role: string): string {
  const roleColors: Record<string, string> = {
    user: 'text-dark-300',
    auditor: 'text-accent-400',
    admin: 'text-warning',
  };
  return roleColors[role] || 'text-dark-300';
}

/**
 * 상태 색상
 */
export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    success: 'text-success',
    fail: 'text-error',
    denied: 'text-warning',
    pending: 'text-dark-400',
  };
  return statusColors[status] || 'text-dark-400';
}

/**
 * 텍스트 자르기
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
