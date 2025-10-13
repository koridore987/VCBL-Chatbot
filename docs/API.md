# API 문서

## 기본 정보

- **Base URL**: `http://localhost:8080/api` (로컬), `https://your-service.run.app/api` (프로덕션)
- **인증**: JWT Bearer Token
- **응답 형식**: JSON

## 인증

대부분의 엔드포인트는 JWT 토큰이 필요합니다.

```http
Authorization: Bearer <your-jwt-token>
```

---

## 인증 API (`/api/auth`)

### 회원가입

```http
POST /api/auth/register
Content-Type: application/json

{
  "student_id": "2024001",
  "password": "password123",
  "name": "홍길동"
}
```

**응답**:
```json
{
  "message": "회원가입이 완료되었습니다",
  "user": {
    "id": 1,
    "student_id": "2024001",
    "name": "홍길동",
    "role": "user",
    "is_active": true
  }
}
```

### 로그인

```http
POST /api/auth/login
Content-Type: application/json

{
  "student_id": "2024001",
  "password": "password123"
}
```

**응답**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "student_id": "2024001",
    "name": "홍길동",
    "role": "user"
  }
}
```

### 현재 사용자 정보

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**응답**:
```json
{
  "id": 1,
  "student_id": "2024001",
  "name": "홍길동",
  "role": "user",
  "daily_token_usage": 1250,
  "total_token_usage": 15600
}
```

---

## 비디오 API (`/api/videos`)

### 비디오 목록 조회

```http
GET /api/videos
Authorization: Bearer <token>
```

**응답**:
```json
[
  {
    "id": 1,
    "title": "인공지능 기초",
    "youtube_url": "https://youtube.com/watch?v=xxxxx",
    "youtube_id": "xxxxx",
    "description": "AI의 기본 개념을 학습합니다",
    "scaffolding_mode": "both",
    "is_active": true
  }
]
```

### 비디오 상세 조회

```http
GET /api/videos/:id
Authorization: Bearer <token>
```

**응답**:
```json
{
  "id": 1,
  "title": "인공지능 기초",
  "scaffoldings": [
    {
      "id": 1,
      "title": "질문 1",
      "prompt_text": "AI의 정의는 무엇인가요?",
      "user_response": {
        "id": 1,
        "response_text": "인공지능은..."
      }
    }
  ]
}
```

### 스캐폴딩 응답 저장

```http
POST /api/videos/:videoId/scaffoldings/:scaffoldingId/respond
Authorization: Bearer <token>
Content-Type: application/json

{
  "response_text": "인공지능은 인간의 지능을 모방하는 기술입니다..."
}
```

### 이벤트 로깅

```http
POST /api/videos/:id/event
Authorization: Bearer <token>
Content-Type: application/json

{
  "event_type": "video_play",
  "event_data": {
    "timestamp": 0,
    "video_time": 120
  }
}
```

---

## 채팅 API (`/api/chat`)

### 채팅 세션 생성

```http
POST /api/chat/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "video_id": 1
}
```

**응답**:
```json
{
  "id": 1,
  "user_id": 1,
  "video_id": 1,
  "total_tokens": 0,
  "total_cost": 0,
  "messages": []
}
```

### 세션 조회

```http
GET /api/chat/sessions/:id
Authorization: Bearer <token>
```

### 메시지 전송

```http
POST /api/chat/sessions/:id/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "AI에 대해 설명해주세요"
}
```

**응답**:
```json
{
  "message": {
    "id": 2,
    "role": "assistant",
    "content": "인공지능은...",
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  },
  "session": {
    "total_tokens": 700,
    "total_cost": 0.00042,
    "summary_updated": false
  }
}
```

---

## 관리자 API (`/api/admin`)

⚠️ 모든 엔드포인트는 **관리자 권한** 필요

### 사용자 관리

#### 사용자 목록

```http
GET /api/admin/users
Authorization: Bearer <admin-token>
```

#### 권한 변경 (Super Admin만)

```http
PUT /api/admin/users/:id/role
Authorization: Bearer <super-admin-token>
Content-Type: application/json

{
  "role": "admin"
}
```

#### 활성화/비활성화

```http
PUT /api/admin/users/:id/activate
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "is_active": false
}
```

#### 비밀번호 재설정

```http
POST /api/admin/users/:id/reset-password
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "new_password": "newpassword123"
}
```

### 비디오 관리

#### 비디오 생성

```http
POST /api/admin/videos
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "title": "새 강의",
  "youtube_url": "https://youtube.com/watch?v=xxxxx",
  "youtube_id": "xxxxx",
  "description": "설명",
  "scaffolding_mode": "both",
  "order_index": 0
}
```

#### 비디오 수정

```http
PUT /api/admin/videos/:id
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "title": "수정된 제목",
  "scaffolding_mode": "chat"
}
```

#### 비디오 삭제

```http
DELETE /api/admin/videos/:id
Authorization: Bearer <admin-token>
```

### 프롬프트 관리

#### 프롬프트 목록

```http
GET /api/admin/prompts
Authorization: Bearer <admin-token>
```

#### 프롬프트 생성

```http
POST /api/admin/prompts
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "수학 학습 프롬프트",
  "description": "수학 과목용 AI 조교",
  "system_prompt": "당신은 수학 학습을 돕는 AI입니다...",
  "constraints": "{\"max_length\": 500}",
  "video_id": 1,
  "user_role": "user",
  "is_default": false
}
```

#### 프롬프트 수정

```http
PUT /api/admin/prompts/:id
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "system_prompt": "수정된 프롬프트...",
  "is_active": true
}
```

---

## 로그 API (`/api/logs`)

⚠️ 관리자 권한 필요

### 이벤트 로그 조회

```http
GET /api/logs/events?page=1&per_page=50&event_type=video_play&user_id=1
Authorization: Bearer <admin-token>
```

**응답**:
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "video_id": 1,
      "event_type": "video_play",
      "event_data": "{}",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 100,
  "pages": 2,
  "current_page": 1
}
```

### CSV 다운로드

```http
GET /api/logs/events/export?event_type=chat_message&start_date=2024-01-01
Authorization: Bearer <admin-token>
```

**응답**: CSV 파일 다운로드

### 채팅 로그 CSV 다운로드

```http
GET /api/logs/chat-sessions/export?user_id=1
Authorization: Bearer <admin-token>
```

### 통계 정보

```http
GET /api/logs/stats
Authorization: Bearer <admin-token>
```

**응답**:
```json
{
  "users": {
    "total": 50,
    "active": 45
  },
  "tokens": {
    "total": 1500000
  },
  "chat": {
    "sessions": 200,
    "messages": 3500
  },
  "events": {
    "total": 10000
  }
}
```

---

## 에러 응답

모든 API는 다음 형식의 에러 응답을 반환합니다:

```json
{
  "error": "에러 메시지"
}
```

### 상태 코드

- `200`: 성공
- `201`: 생성 성공
- `400`: 잘못된 요청
- `401`: 인증 실패
- `403`: 권한 없음
- `404`: 리소스 없음
- `409`: 충돌 (예: 중복 학번)
- `429`: 요청 제한 초과 (토큰 한도)
- `500`: 서버 오류

---

## 제한사항

- **일일 토큰 한도**: 50,000 토큰/사용자
- **요청 크기**: 최대 4,000 토큰 입력
- **응답 크기**: 최대 1,000 토큰 출력
- **요약 생성 트리거**: 세션 3,500 토큰 초과 시

---

## 예제 코드

### JavaScript (Axios)

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 로그인
const login = async (studentId, password) => {
  const response = await api.post('/auth/login', {
    student_id: studentId,
    password
  })
  
  // 토큰 저장
  localStorage.setItem('token', response.data.access_token)
}

// 인증 요청
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 비디오 목록 조회
const videos = await api.get('/videos')
```

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:8080/api'

# 로그인
response = requests.post(f'{BASE_URL}/auth/login', json={
    'student_id': '2024001',
    'password': 'password123'
})

token = response.json()['access_token']

# 인증 헤더
headers = {
    'Authorization': f'Bearer {token}'
}

# 비디오 목록 조회
videos = requests.get(f'{BASE_URL}/videos', headers=headers).json()
```

