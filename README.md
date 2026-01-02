# AI Platform - MCP 기반 감사 로깅 시스템

기업용 AI 플랫폼으로, MCP(Model Context Protocol)를 통한 데이터 접근을 감사 로깅합니다.

## 아키텍처

```
[사용자] → [AI 플랫폼] → [Gemini API]
                ↓
        [MCP Gateway] → [MySQL/Notion/Calendar MCP]
                ↓
        [Audit Logger] → [PostgreSQL]
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | Python + FastAPI |
| 프론트엔드 | Next.js 14 + Tailwind CSS |
| DB | PostgreSQL (감사로그), MySQL (MCP) |
| LLM | Gemini API |
| 상태관리 | Zustand |

## 구현 단계

- [x] **1단계**: MCP Gateway + 감사 로깅
- [x] **2단계**: AI Agent (Gemini 연동)
- [x] **3단계**: 대화 관리
- [x] **4단계**: 인증/인가
- [x] **5단계**: 관리자 기능

## 빠른 시작

### 1. Docker Compose로 실행

```bash
# 프로젝트 루트에서
docker-compose up -d

# API 확인
curl http://localhost:8000/health
```

### 2. 로컬 개발 환경

```bash
# PostgreSQL, MySQL 실행 (Docker)
docker-compose up -d postgres mysql

# 백엔드 실행
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 필요시 수정
uvicorn app.main:app --reload

# 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm run dev
```

### 3. 접속 URL

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| 백엔드 API | http://localhost:8000 |
| API 문서 | http://localhost:8000/docs |
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env 설정
cp .env.example .env
# .env 파일 수정

# 서버 실행
uvicorn app.main:app --reload
```

## API 엔드포인트

### MCP Gateway

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/mcp/connections` | MCP 연결 생성 |
| GET | `/api/mcp/connections` | 연결 목록 조회 |
| DELETE | `/api/mcp/connections/{id}` | 연결 해제 |
| GET | `/api/mcp/tools` | Tool 목록 조회 |
| POST | `/api/mcp/call` | Tool 호출 |

### 감사 로그

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/audit/logs` | 로그 목록 (필터 지원) |
| GET | `/api/audit/logs/{id}` | 로그 상세 |
| GET | `/api/audit/stats` | 통계 조회 |

### AI Agent

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/agent/chat` | AI 채팅 메시지 처리 |
| POST | `/api/agent/chat/stream` | 스트리밍 응답 |
| GET | `/api/agent/status` | Agent 상태 확인 |
| POST | `/api/agent/sync-tools` | Tool 목록 동기화 |

### 대화 관리 (Chat)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat/sessions` | 새 세션 생성 |
| GET | `/api/chat/sessions` | 세션 목록 조회 |
| GET | `/api/chat/sessions/{id}` | 세션 상세 (메시지 포함) |
| PATCH | `/api/chat/sessions/{id}` | 세션 제목 수정 |
| DELETE | `/api/chat/sessions/{id}` | 세션 삭제 |
| POST | `/api/chat/sessions/{id}/messages` | 메시지 전송 (AI 응답) |
| GET | `/api/chat/sessions/{id}/messages` | 메시지 목록 |
| POST | `/api/chat/quick` | 빠른 채팅 (세션 자동 생성) |

### 인증 (Auth)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| POST | `/api/auth/register` | 회원가입 | - |
| POST | `/api/auth/login` | 로그인 | - |
| POST | `/api/auth/refresh` | 토큰 갱신 | - |
| GET | `/api/auth/me` | 내 정보 조회 | User |
| POST | `/api/auth/me/change-password` | 비밀번호 변경 | User |
| GET | `/api/auth/users` | 사용자 목록 | Admin |
| PATCH | `/api/auth/users/{id}/role` | 역할 변경 | Admin |
| POST | `/api/auth/users/{id}/deactivate` | 사용자 비활성화 | Admin |
| POST | `/api/auth/users/{id}/activate` | 사용자 활성화 | Admin |

### 인증된 채팅 (Chat Auth)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat/auth/sessions` | 새 세션 생성 (인증) |
| GET | `/api/chat/auth/sessions` | 내 세션 목록 |
| GET | `/api/chat/auth/sessions/{id}` | 세션 상세 |
| DELETE | `/api/chat/auth/sessions/{id}` | 세션 삭제 |
| POST | `/api/chat/auth/sessions/{id}/messages` | 메시지 전송 |

### 관리자 (Admin)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/admin/dashboard` | 대시보드 통계 | Admin |
| GET | `/api/admin/stats/daily` | 일별 통계 | Admin |
| GET | `/api/admin/stats/users` | 사용자별 활동 | Admin |
| GET | `/api/admin/mcp/connections` | MCP 연결 목록 | Admin |
| POST | `/api/admin/mcp/connections/{id}/enable` | MCP 활성화 | Admin |
| POST | `/api/admin/mcp/connections/{id}/disable` | MCP 비활성화 | Admin |
| GET | `/api/admin/audit/logs` | 전체 감사 로그 | Auditor |
| GET | `/api/admin/audit/logs/{id}` | 로그 상세 | Auditor |
| GET | `/api/admin/audit/export` | 로그 내보내기 | Auditor |
| GET | `/api/admin/settings` | 시스템 설정 | Admin |
| GET | `/api/admin/health/detailed` | 상세 상태 | Admin |

## 사용 예시

### 1. MySQL MCP 연결

```bash
curl -X POST http://localhost:8000/api/mcp/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test DB",
    "type": "mysql",
    "config": {
      "host": "localhost",
      "port": 3306,
      "user": "testuser",
      "password": "testpassword",
      "database": "testdb"
    }
  }'
```

### 2. Tool 호출

```bash
curl -X POST http://localhost:8000/api/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "mysql.query",
    "params": {
      "sql": "SELECT * FROM customers LIMIT 5"
    },
    "user_query": "고객 목록 보여줘"
  }'
```

### 3. 감사 로그 조회

```bash
# 전체 로그
curl http://localhost:8000/api/audit/logs

# 키워드 검색 (예: 특정 고객 ID)
curl "http://localhost:8000/api/audit/logs?keyword=C001"

# 사용자별 필터
curl "http://localhost:8000/api/audit/logs?user_id=kim"
```

### 4. AI 채팅 (Agent)

```bash
# Agent 상태 확인
curl http://localhost:8000/api/agent/status

# AI 채팅 (Simple 모드 - Gemini API 없이)
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "고객 목록 보여줘"
  }'

# AI 채팅 (히스토리 포함)
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "삼성전자 주문 내역 알려줘",
    "history": [
      {"role": "user", "content": "고객 목록 보여줘"},
      {"role": "assistant", "content": "총 5건의 고객 데이터..."}
    ]
  }'
```

#### Gemini API 사용 시

```bash
# .env에 API 키 설정
GEMINI_API_KEY=your_api_key_here

# Tool 동기화
curl -X POST http://localhost:8000/api/agent/sync-tools

# 자연어로 질문
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "지난달 매출이 가장 높은 고객 3명 알려줘"
  }'
```

### 5. 대화 관리 (세션 기반)

```bash
# 새 세션 생성
curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "고객 분석"}'

# 세션 목록 조회
curl http://localhost:8000/api/chat/sessions

# 세션에 메시지 전송 (AI 응답 포함)
curl -X POST http://localhost:8000/api/chat/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "고객 목록 보여줘"}'

# 세션 상세 조회 (전체 대화 내역)
curl http://localhost:8000/api/chat/sessions/{session_id}

# 빠른 채팅 (세션 자동 생성)
curl -X POST http://localhost:8000/api/chat/quick \
  -H "Content-Type: application/json" \
  -d '{"message": "테이블 목록 보여줘"}'
```

### 6. 인증 (Auth)

```bash
# 회원가입
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "홍길동"
  }'

# 로그인
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# 응답에서 access_token 획득 후 사용
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# 내 정보 조회
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 인증된 채팅
curl -X POST http://localhost:8000/api/chat/auth/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "내 대화"}'
```

#### 역할 (Role)

| 역할 | 권한 |
|------|------|
| User | 채팅, 본인 세션 관리 |
| Auditor | User + 전체 감사 로그 조회 |
| Admin | Auditor + 사용자 관리 |

### 7. 관리자 기능 (Admin)

```bash
# Admin 계정으로 로그인 후 토큰 획득
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# 대시보드 통계
curl http://localhost:8000/api/admin/dashboard \
  -H "Authorization: Bearer $TOKEN"

# 일별 통계 (최근 7일)
curl "http://localhost:8000/api/admin/stats/daily?days=7" \
  -H "Authorization: Bearer $TOKEN"

# 사용자별 활동 통계
curl http://localhost:8000/api/admin/stats/users \
  -H "Authorization: Bearer $TOKEN"

# 전체 감사 로그 조회 (Auditor 이상)
curl "http://localhost:8000/api/admin/audit/logs?limit=20" \
  -H "Authorization: Bearer $TOKEN"

# 감사 로그 내보내기 (CSV)
curl "http://localhost:8000/api/admin/audit/export?format=csv" \
  -H "Authorization: Bearer $TOKEN"

# MCP 연결 관리
curl http://localhost:8000/api/admin/mcp/connections \
  -H "Authorization: Bearer $TOKEN"

# 시스템 설정 조회
curl http://localhost:8000/api/admin/settings \
  -H "Authorization: Bearer $TOKEN"

# 상세 시스템 상태
curl http://localhost:8000/api/admin/health/detailed \
  -H "Authorization: Bearer $TOKEN"
```

## 디렉토리 구조

```
ai-platform/
├── backend/
│   ├── app/
│   │   ├── audit/              # 감사 로깅 (1단계)
│   │   │   ├── masking.py      # 민감정보 마스킹
│   │   │   ├── service.py      # 로깅 서비스
│   │   │   └── router.py       # API 라우터
│   │   ├── mcp_gateway/        # MCP Gateway (1단계)
│   │   │   ├── gateway.py      # 게이트웨이 코어
│   │   │   ├── mysql_client.py # MySQL MCP 클라이언트
│   │   │   └── router.py       # API 라우터
│   │   ├── agent/              # AI Agent (2단계) ✅
│   │   │   ├── gemini_client.py # Gemini API 클라이언트
│   │   │   ├── service.py      # Agent 서비스
│   │   │   └── router.py       # API 라우터
│   │   ├── chat/               # 대화 관리 (3단계) ✅
│   │   │   ├── service.py      # 세션/메시지 서비스
│   │   │   ├── router.py       # API 라우터
│   │   │   └── router_auth.py  # 인증된 API 라우터
│   │   ├── auth/               # 인증 (4단계) ✅
│   │   │   ├── utils.py        # 비밀번호/JWT 유틸
│   │   │   ├── service.py      # 인증 서비스
│   │   │   ├── dependencies.py # FastAPI 의존성
│   │   │   └── router.py       # API 라우터
│   │   ├── admin/              # 관리자 (5단계) ✅
│   │   │   ├── service.py      # 대시보드/통계 서비스
│   │   │   └── router.py       # API 라우터
│   │   ├── models/             # DB 모델
│   │   ├── config/             # 설정
│   │   └── main.py             # FastAPI 앱
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # 프론트엔드 ✅
│   ├── app/
│   │   ├── auth/               # 로그인/회원가입
│   │   ├── chat/               # 채팅 페이지
│   │   ├── admin/              # 관리자 대시보드
│   │   ├── layout.tsx          # 루트 레이아웃
│   │   ├── globals.css         # 글로벌 스타일
│   │   └── page.tsx            # 메인 페이지
│   ├── components/
│   │   ├── ui/                 # 공통 UI 컴포넌트
│   │   └── chat/               # 채팅 컴포넌트
│   ├── lib/
│   │   ├── api.ts              # API 클라이언트
│   │   ├── store.ts            # 상태 관리
│   │   └── utils.ts            # 유틸리티
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
└── init-mysql.sql              # 테스트 데이터
```

## 민감정보 마스킹

감사 로그 저장 시 자동 마스킹:

| 데이터 | 원본 | 마스킹 결과 |
|--------|------|-------------|
| 주민번호 | 900101-1234567 | ******-******* |
| 카드번호 | 1234-5678-9012-3456 | ****-****-****-3456 |
| 이메일 | kim@company.com | k**@company.com |
| 전화번호 | 010-1234-5678 | 010-****-5678 |

## 테스트

```bash
cd backend
pytest -v
```

## 라이선스

MIT
