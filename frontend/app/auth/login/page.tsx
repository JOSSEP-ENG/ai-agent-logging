'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Bot, Mail, Lock, ArrowRight, Sparkles } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { authApi, ApiError } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      await authApi.login(email, password);
      router.push('/chat');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('로그인에 실패했습니다');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen flex">
      {/* 왼쪽: 브랜딩 영역 */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-dark-900 via-dark-800 to-accent-900/20 relative overflow-hidden">
        {/* 배경 장식 */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-600/10 rounded-full blur-3xl" />
        </div>
        
        {/* 콘텐츠 */}
        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-accent-500 rounded-xl flex items-center justify-center">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">AI Platform</span>
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            기업 데이터에<br />
            <span className="text-gradient">AI의 힘을</span> 더하다
          </h1>
          
          <p className="text-dark-300 text-lg mb-8 max-w-md">
            자연어로 데이터베이스를 조회하고, 
            모든 접근 이력을 안전하게 감사 로깅합니다.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-dark-200">
              <Sparkles className="w-5 h-5 text-accent-400" />
              <span>Gemini AI 기반 자연어 처리</span>
            </div>
            <div className="flex items-center gap-3 text-dark-200">
              <Sparkles className="w-5 h-5 text-accent-400" />
              <span>MCP 프로토콜로 안전한 데이터 연결</span>
            </div>
            <div className="flex items-center gap-3 text-dark-200">
              <Sparkles className="w-5 h-5 text-accent-400" />
              <span>민감정보 자동 마스킹 & 감사 로깅</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* 오른쪽: 로그인 폼 */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-8 py-12">
        <div className="w-full max-w-md">
          {/* 모바일용 로고 */}
          <div className="lg:hidden flex items-center gap-3 mb-12 justify-center">
            <div className="w-10 h-10 bg-accent-500 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AI Platform</span>
          </div>
          
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">로그인</h2>
            <p className="text-dark-400">계정에 로그인하여 시작하세요</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
                {error}
              </div>
            )}
            
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
              <input
                type="email"
                placeholder="이메일"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input pl-12"
                required
              />
            </div>
            
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
              <input
                type="password"
                placeholder="비밀번호"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input pl-12"
                required
              />
            </div>
            
            <Button 
              type="submit" 
              className="w-full" 
              size="lg"
              isLoading={isLoading}
            >
              로그인
              <ArrowRight className="w-5 h-5" />
            </Button>
          </form>
          
          <div className="mt-6 text-center text-dark-400">
            계정이 없으신가요?{' '}
            <Link href="/auth/register" className="text-accent-400 hover:text-accent-300 font-medium">
              회원가입
            </Link>
          </div>
          
          {/* 테스트 계정 안내 */}
          <div className="mt-8 p-4 bg-dark-800/50 rounded-lg border border-dark-700">
            <p className="text-sm text-dark-400 mb-2">테스트 계정</p>
            <p className="text-sm text-dark-300">
              인증 없이 사용하려면{' '}
              <Link href="/chat" className="text-accent-400 hover:underline">
                바로 채팅 시작
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
