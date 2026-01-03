/**
 * 인증 상태 관리 스토어
 */
import { create } from 'zustand';
import { authApi, User } from './api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  
  // 액션
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  
  setUser: (user) => {
    set({ user, isAuthenticated: !!user });
  },
  
  login: async (email, password) => {
    const response = await authApi.login(email, password);
    set({
      user: response.user as User,
      isAuthenticated: true,
      isLoading: false,
    });
  },
  
  logout: () => {
    authApi.logout();
    set({ user: null, isAuthenticated: false });
  },
  
  checkAuth: async () => {
    set({ isLoading: true });
    
    try {
      const token = typeof window !== 'undefined' 
        ? localStorage.getItem('access_token') 
        : null;
      
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      // 토큰 만료 시 리프레시 시도
      try {
        await authApi.refresh();
        const user = await authApi.getMe();
        set({ user, isAuthenticated: true, isLoading: false });
      } catch {
        authApi.logout();
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    }
  },
}));
