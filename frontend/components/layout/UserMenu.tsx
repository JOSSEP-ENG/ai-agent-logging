'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { User, Settings, LogOut, ChevronUp } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { cn } from '@/lib/utils';

interface UserMenuProps {
  isExpanded: boolean;
}

export function UserMenu({ isExpanded }: UserMenuProps) {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
    setShowUserMenu(false);
  };

  if (!user) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setShowUserMenu(!showUserMenu)}
        className="w-full p-3 hover:bg-dark-800 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-3">
          {/* 사용자 아바타 */}
          <div className="w-8 h-8 bg-accent-500 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm font-bold">
              {user.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>

          {/* 사용자 정보 (펼쳤을 때만) */}
          {isExpanded && (
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name}</p>
              <p className="text-xs text-dark-500 truncate">{user.email}</p>
            </div>
          )}

          {/* 드롭다운 아이콘 (펼쳤을 때만) */}
          {isExpanded && (
            <ChevronUp
              className={cn(
                'w-4 h-4 text-dark-500 transition-transform flex-shrink-0',
                showUserMenu && 'rotate-180'
              )}
            />
          )}
        </div>
      </button>

      {/* 위로 펼쳐지는 드롭다운 */}
      {showUserMenu && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-dark-800 rounded-lg shadow-xl border border-dark-700 py-1 z-50">
          <button
            onClick={() => {
              router.push('/profile');
              setShowUserMenu(false);
            }}
            className="w-full px-4 py-2 text-left text-sm text-dark-200 hover:bg-dark-700 transition-colors flex items-center gap-2"
          >
            <User className="w-4 h-4" />
            프로필
          </button>
          <button
            onClick={() => {
              router.push('/preferences');
              setShowUserMenu(false);
            }}
            className="w-full px-4 py-2 text-left text-sm text-dark-200 hover:bg-dark-700 transition-colors flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            환경 설정
          </button>
          <div className="border-t border-dark-700 my-1" />
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 text-left text-sm text-error hover:bg-dark-700 transition-colors flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
