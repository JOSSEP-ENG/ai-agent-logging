'use client';

import { useState, useEffect } from 'react';
import { ChatSidebar, ChatMessages, ChatInput } from '@/components/chat';
import { chatApi, Message, ChatResponse } from '@/lib/api';

export default function ChatPage() {
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // 세션 선택 시 메시지 로드
  const handleSessionSelect = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setIsLoading(true);
    
    try {
      const response = await chatApi.getSession(sessionId);
      setMessages(response.messages);
    } catch (error) {
      console.error('Failed to load session:', error);
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 새 대화 시작
  const handleNewChat = () => {
    setCurrentSessionId(undefined);
    setMessages([]);
  };
  
  // 메시지 전송
  const handleSendMessage = async (content: string) => {
    // 사용자 메시지 즉시 표시
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId || '',
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      let response: ChatResponse;
      
      if (currentSessionId) {
        // 기존 세션에 메시지 전송
        response = await chatApi.sendMessage(currentSessionId, content);
      } else {
        // 새 세션 생성 (quick chat)
        response = await chatApi.quickChat(content);
        setCurrentSessionId(response.user_message.session_id);
      }
      
      // 실제 응답으로 메시지 업데이트
      setMessages(prev => {
        const newMessages = prev.filter(m => m.id !== userMessage.id);
        return [
          ...newMessages,
          response.user_message,
          response.assistant_message,
        ];
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // 에러 메시지 추가
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        session_id: currentSessionId || '',
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        created_at: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="flex h-screen bg-dark-900">
      {/* 사이드바 */}
      <ChatSidebar
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
      />
      
      {/* 메인 채팅 영역 */}
      <main className="flex-1 flex flex-col">
        <ChatMessages 
          messages={messages} 
          isLoading={isLoading}
        />
        
        <ChatInput 
          onSend={handleSendMessage}
          disabled={isLoading}
        />
      </main>
    </div>
  );
}
