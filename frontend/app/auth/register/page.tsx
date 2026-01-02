'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Bot, Mail, Lock, User, ArrowRight, Check } from 'lucide-react';
import { Button } from '@/components/ui';
import { authApi, ApiError } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // 비밀번호 확인
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다');
      return;
    }
    
    if (password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다');
      return;
    }
    
    setIsLoading(true);
    
    try {
      await authApi.register(email, password, name);
      // 회원가입 성공 후 로그인
      await authApi.login(email, password);
      router.push('/chat');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('회원가입에 실패했습니다');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  const passwordRequirements = [
    { met: password.length >= 8, text: '8자 이상' },
  ];
  
  return (
    <div className="min-h-screen flex">
      {/* 왼쪽: 브랜딩 영역 */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-dark-900 via-dark-800 to-accent-900/20 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-600/10 rounded-full blur-3xl" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-accent-500 rounded-xl flex items-center justify-center">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">AI Platform</span>
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            간편하게 가입하고<br />
            <span className="text-gradient">AI와 대화</span>를 시작하세요
          </h1>
          
          <p className="text-dark-300 text-lg mb-8 max-w-md">
            회원가입 후 바로 데이터베이스 연결과 
            AI 채팅을 시작할 수 있습니다.
          </p>
        </div>
      </div>
      
      {/* 오른쪽: 회원가입 폼 */}
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
            <h2 className="text-2xl font-bold text-white mb-2">회원가입</h2>
            <p className="text-dark-400">새 계정을 만들어 시작하세요</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
                {error}
              </div>
            )}
            
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
              <input
                type="text"
                placeholder="이름"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input pl-12"
                required
              />
            </div>
            
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
            
            {/* 비밀번호 요구사항 */}
            {password && (
              <div className="space-y-1">
                {passwordRequirements.map((req, index) => (
                  <div 
                    key={index}
                    className={`flex items-center gap-2 text-sm ${
                      req.met ? 'text-success' : 'text-dark-500'
                    }`}
                  >
                    <Check className="w-4 h-4" />
                    <span>{req.text}</span>
                  </div>
                ))}
              </div>
            )}
            
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
              <input
                type="password"
                placeholder="비밀번호 확인"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
              회원가입
              <ArrowRight className="w-5 h-5" />
            </Button>
          </form>
          
          <div className="mt-6 text-center text-dark-400">
            이미 계정이 있으신가요?{' '}
            <Link href="/auth/login" className="text-accent-400 hover:text-accent-300 font-medium">
              로그인
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
