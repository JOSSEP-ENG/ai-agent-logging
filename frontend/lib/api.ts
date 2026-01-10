/**
 * API 클라이언트
 * 
 * 백엔드 API와 통신하는 함수들
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// ============ 타입 정의 ============

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'auditor' | 'admin';
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Session {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count?: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  args: Record<string, any>;
  result?: any;
  error?: string;
  success: boolean;
}

export interface ChatResponse {
  user_message: Message;
  assistant_message: Message;
  tool_calls: ToolCall[];
  execution_time_ms: number;
}

export interface DashboardStats {
  users: {
    total: number;
    active: number;
    inactive: number;
    by_role: Record<string, number>;
    new_last_7_days: number;
  };
  sessions: {
    total: number;
    active: number;
    total_messages: number;
    today_sessions: number;
    avg_messages_per_session: number;
  };
  audit: {
    total: number;
    by_status: Record<string, number>;
    today_logs: number;
    top_tools: { tool: string; count: number }[];
    success_rate: number;
  };
  system: {
    status: string;
    database: string;
    uptime: string;
  };
}

export interface MCPConnection {
  id: string;
  name: string;
  type: string;
  description?: string;
  is_active: boolean;
  last_tested_at?: string;
  last_test_status?: string;
  created_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  tools_count?: number;
  error?: string;
}

// ============ API 에러 ============

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

// ============ 헬퍼 함수 ============

function getAuthHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  
  const token = localStorage.getItem('access_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }
  
  return response.json();
}

// ============ Auth API ============

export const authApi = {
  async register(email: string, password: string, name: string): Promise<User> {
    return fetchApi('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
  },
  
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetchApi<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    // 토큰 저장
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    
    return response;
  },
  
  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  async getMe(): Promise<User> {
    return fetchApi('/api/auth/me');
  },
  
  async refresh(): Promise<{ access_token: string }> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new ApiError(401, 'No refresh token');
    }
    
    const response = await fetchApi<{ access_token: string }>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    localStorage.setItem('access_token', response.access_token);
    return response;
  },
};

// ============ Chat API ============

export const chatApi = {
  async getSessions(limit = 20): Promise<{ sessions: Session[]; total: number }> {
    return fetchApi(`/api/chat/auth/sessions?limit=${limit}`);
  },

  async createSession(title?: string): Promise<Session> {
    return fetchApi('/api/chat/auth/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  async getSession(sessionId: string): Promise<{ session: Session; messages: Message[] }> {
    return fetchApi(`/api/chat/auth/sessions/${sessionId}`);
  },

  async deleteSession(sessionId: string): Promise<void> {
    await fetchApi(`/api/chat/auth/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  async sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
    return fetchApi(`/api/chat/auth/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },

  async quickChat(message: string): Promise<ChatResponse> {
    // 첫 메시지의 앞 50자를 제목으로 사용
    const title = message.length > 50 ? message.substring(0, 50) + '...' : message;

    return fetchApi<Session>('/api/chat/auth/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }).then(async (session: Session) => {
      return fetchApi<ChatResponse>(`/api/chat/auth/sessions/${session.id}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
    });
  },
};

// ============ MCP API ============

export const mcpApi = {
  async getUserConnections(): Promise<MCPConnection[]> {
    return fetchApi('/api/mcp/connections');
  },

  async createConnection(
    name: string,
    type: string,
    config: Record<string, any>,
    credentials: Record<string, any>,
  ): Promise<MCPConnection> {
    return fetchApi('/api/mcp/connections', {
      method: 'POST',
      body: JSON.stringify({ name, type, config, credentials }),
    });
  },

  async deleteConnection(connectionId: string): Promise<void> {
    await fetchApi(`/api/mcp/connections/${connectionId}`, {
      method: 'DELETE',
    });
  },

  async testConnection(connectionId: string): Promise<ConnectionTestResult> {
    return fetchApi(`/api/mcp/connections/${connectionId}/test`, {
      method: 'POST',
    });
  },

  async getTools(): Promise<{ tools: any[] }> {
    return fetchApi('/api/mcp/tools');
  },
};

// ============ Admin API ============

export const adminApi = {
  async getDashboard(): Promise<DashboardStats> {
    return fetchApi('/api/admin/dashboard');
  },
  
  async getDailyStats(days = 7): Promise<any[]> {
    return fetchApi(`/api/admin/stats/daily?days=${days}`);
  },
  
  async getUserActivity(limit = 10): Promise<any[]> {
    return fetchApi(`/api/admin/stats/users?limit=${limit}`);
  },
  
  async getAuditLogs(params: {
    limit?: number;
    offset?: number;
    user_id?: string;
    tool_name?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<{ logs: any[]; total: number; limit: number; offset: number }> {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set('limit', params.limit.toString());
    if (params.offset) searchParams.set('offset', params.offset.toString());
    if (params.user_id) searchParams.set('user_id', params.user_id);
    if (params.tool_name) searchParams.set('tool_name', params.tool_name);
    if (params.status) searchParams.set('status', params.status);
    if (params.start_date) searchParams.set('start_date', params.start_date);
    if (params.end_date) searchParams.set('end_date', params.end_date);

    return fetchApi(`/api/admin/audit/logs?${searchParams}`);
  },
  
  async getUsers(): Promise<{ users: User[]; total: number }> {
    return fetchApi('/api/auth/users');
  },
  
  async updateUserRole(userId: string, role: string): Promise<User> {
    return fetchApi(`/api/auth/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    });
  },
};

// ============ User Profile API ============

export interface UpdateProfileRequest {
  name?: string;
  email?: string;
  avatar_url?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UserActivity {
  id: string;
  type: 'login' | 'logout' | 'session_created' | 'settings_changed';
  description: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
}

export const userApi = {
  async updateProfile(data: UpdateProfileRequest): Promise<User> {
    return fetchApi('/api/auth/profile', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    return fetchApi('/api/auth/password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getActivity(limit = 10): Promise<UserActivity[]> {
    return fetchApi(`/api/auth/activity?limit=${limit}`);
  },
};
