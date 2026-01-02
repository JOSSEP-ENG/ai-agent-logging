'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Database, 
  CheckCircle2, 
  XCircle,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui';
import { Message, ToolCall } from '@/lib/api';
import { formatDateTime, cn } from '@/lib/utils';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);
  
  if (messages.length === 0 && !isLoading) {
    return <EmptyState />;
  }
  
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 space-y-6">
      {messages.map((message, index) => (
        <MessageItem 
          key={message.id || index} 
          message={message} 
          animate={index === messages.length - 1}
        />
      ))}
      
      {isLoading && <TypingIndicator />}
      
      <div ref={messagesEndRef} />
    </div>
  );
}

function EmptyState() {
  const suggestions = [
    '테이블 목록 보여줘',
    '고객 목록 조회해줘',
    '최근 주문 내역 알려줘',
    'customers 테이블 구조 보여줘',
  ];
  
  return (
    <div className="flex-1 flex items-center justify-center px-4">
      <div className="max-w-xl text-center">
        <div className="w-16 h-16 bg-accent-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Sparkles className="w-8 h-8 text-accent-400" />
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-3">
          무엇을 도와드릴까요?
        </h2>
        
        <p className="text-dark-400 mb-8">
          자연어로 데이터베이스를 조회하고 분석할 수 있습니다.
          연결된 MCP를 통해 안전하게 데이터에 접근합니다.
        </p>
        
        <div className="grid grid-cols-2 gap-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="p-3 bg-dark-800 hover:bg-dark-700 border border-dark-700 rounded-lg text-left text-sm text-dark-300 hover:text-dark-100 transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function MessageItem({ message, animate }: { message: Message; animate?: boolean }) {
  const isUser = message.role === 'user';
  
  return (
    <div 
      className={cn(
        'flex gap-4 max-w-4xl mx-auto',
        animate && 'animate-slide-up'
      )}
    >
      {/* 아바타 */}
      <div className={cn(
        'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
        isUser ? 'bg-accent-600' : 'bg-dark-700'
      )}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-accent-400" />
        )}
      </div>
      
      {/* 메시지 내용 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-dark-200">
            {isUser ? '나' : 'AI'}
          </span>
          <span className="text-xs text-dark-500">
            {formatDateTime(message.created_at)}
          </span>
        </div>
        
        <div className={cn(
          'prose prose-invert max-w-none',
          'text-dark-200 text-[15px] leading-relaxed'
        )}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {/* Tool 호출 정보 */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.tool_calls.map((tool, index) => (
              <ToolCallItem key={index} tool={tool} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallItem({ tool }: { tool: ToolCall }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="bg-dark-800/50 border border-dark-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 px-3 py-2 hover:bg-dark-800/50 transition-colors"
      >
        <Database className="w-4 h-4 text-accent-400 flex-shrink-0" />
        <span className="text-sm text-dark-300 flex-1 text-left font-mono">
          {tool.name}
        </span>
        {tool.success ? (
          <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
        ) : (
          <XCircle className="w-4 h-4 text-error flex-shrink-0" />
        )}
        <ChevronDown className={cn(
          'w-4 h-4 text-dark-500 transition-transform',
          isExpanded && 'rotate-180'
        )} />
      </button>
      
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {/* 파라미터 */}
          {Object.keys(tool.args).length > 0 && (
            <div>
              <p className="text-xs text-dark-500 mb-1">Parameters</p>
              <pre className="text-xs text-dark-400 bg-dark-900 p-2 rounded overflow-x-auto">
                {JSON.stringify(tool.args, null, 2)}
              </pre>
            </div>
          )}
          
          {/* 결과 또는 에러 */}
          {tool.error ? (
            <div>
              <p className="text-xs text-error mb-1">Error</p>
              <p className="text-xs text-dark-400">{tool.error}</p>
            </div>
          ) : tool.result && (
            <div>
              <p className="text-xs text-dark-500 mb-1">Result</p>
              <pre className="text-xs text-dark-400 bg-dark-900 p-2 rounded overflow-x-auto max-h-48">
                {JSON.stringify(tool.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-4 max-w-4xl mx-auto animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 bg-dark-700 rounded-lg flex items-center justify-center">
        <Bot className="w-4 h-4 text-accent-400" />
      </div>
      <div className="flex items-center gap-1 py-3">
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}

// ============ 입력 영역 ============

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || disabled) return;
    
    onSend(message.trim());
    setMessage('');
    
    // 높이 리셋
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };
  
  return (
    <div className="border-t border-dark-800 p-4">
      <form 
        onSubmit={handleSubmit}
        className="max-w-4xl mx-auto relative"
      >
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="메시지를 입력하세요..."
          disabled={disabled}
          rows={1}
          className={cn(
            'w-full px-4 py-3 pr-14 bg-dark-800 border border-dark-700 rounded-xl',
            'text-dark-100 placeholder:text-dark-500 resize-none',
            'focus:outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500/50',
            'transition-all duration-200',
            'scrollbar-thin'
          )}
        />
        
        <Button
          type="submit"
          size="sm"
          disabled={!message.trim() || disabled}
          className="absolute right-2 bottom-2"
        >
          <Send className="w-4 h-4" />
        </Button>
      </form>
      
      <p className="text-xs text-dark-500 text-center mt-2">
        AI는 실수할 수 있습니다. 중요한 정보는 확인하세요.
      </p>
    </div>
  );
}
