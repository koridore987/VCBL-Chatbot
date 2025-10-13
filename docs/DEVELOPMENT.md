# 개발 가이드

## 개발 환경 설정

### 필수 요구사항

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose

### 초기 설정

```bash
# 저장소 클론
git clone <repository-url>
cd VCBL-Chatbot

# 환경 변수 설정
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env

# Docker Compose로 전체 스택 실행
docker-compose up -d

# Super Admin 생성
docker-compose exec backend bash scripts/create-admin.sh admin001 "관리자" admin123
```

## Backend 개발

### 가상 환경 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 데이터베이스 마이그레이션

```bash
# 초기 마이그레이션
flask db init

# 마이그레이션 생성
flask db migrate -m "설명"

# 마이그레이션 적용
flask db upgrade

# 롤백
flask db downgrade
```

### 새 모델 추가

1. `backend/app/models/`에 모델 파일 생성
2. `backend/app/models/__init__.py`에 import 추가
3. 마이그레이션 생성 및 적용

예시:
```python
# backend/app/models/new_model.py
from app import db
from datetime import datetime

class NewModel(db.Model):
    __tablename__ = 'new_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 새 API 엔드포인트 추가

1. `backend/app/routes/`에 라우트 파일 생성
2. `backend/app/__init__.py`에 Blueprint 등록

예시:
```python
# backend/app/routes/new_route.py
from flask import Blueprint, jsonify

new_bp = Blueprint('new', __name__)

@new_bp.route('/', methods=['GET'])
def get_items():
    return jsonify([]), 200
```

### 테스트 작성

```bash
# 테스트 실행
pytest

# 커버리지 확인
pytest --cov=app
```

## Frontend 개발

### 개발 서버 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

### 새 페이지 추가

1. `frontend/src/pages/`에 컴포넌트 생성
2. `frontend/src/App.jsx`에 라우트 추가

예시:
```jsx
// frontend/src/pages/NewPage.jsx
const NewPage = () => {
  return <div>New Page</div>
}

export default NewPage

// frontend/src/App.jsx에 추가
<Route path="/new" element={<ProtectedRoute><NewPage /></ProtectedRoute>} />
```

### API 호출

```javascript
import api from '../services/api'

// GET 요청
const response = await api.get('/videos')

// POST 요청
const response = await api.post('/videos', { title: 'New Video' })

// 에러 처리
try {
  const response = await api.get('/videos')
} catch (error) {
  console.error(error.response?.data?.error)
}
```

### 스타일링

- 글로벌 스타일: `frontend/src/index.css`
- 컴포넌트별 인라인 스타일 사용
- 재사용 가능한 CSS 클래스 정의

## 데이터베이스

### ERD (Entity Relationship Diagram)

```
users
  |
  |-- chat_sessions --< chat_messages
  |-- event_logs
  |-- scaffolding_responses
  
videos
  |
  |-- scaffoldings --< scaffolding_responses
  |-- chat_sessions
  |-- event_logs

chat_prompt_templates
  |
  |-- (video_id: optional)
  |-- (created_by: users)
```

### 주요 쿼리 패턴

```python
# 사용자의 특정 비디오 세션 조회
session = ChatSession.query.filter_by(
    user_id=user_id,
    video_id=video_id,
    is_active=True
).first()

# 최근 메시지 조회
recent_messages = ChatMessage.query.filter_by(
    session_id=session_id
).order_by(ChatMessage.created_at.desc()).limit(10).all()

# 이벤트 로그 통계
from sqlalchemy import func

stats = db.session.query(
    func.count(EventLog.id),
    EventLog.event_type
).group_by(EventLog.event_type).all()
```

## OpenAI 서비스

### 요약 생성 로직

```python
# backend/app/services/openai_service.py

# 1. 세션 토큰 확인
if session.total_tokens > SUMMARY_TRIGGER_TOKENS:
    # 2. 오래된 메시지 요약
    messages_to_summarize = session.messages[:-5]
    new_summary = generate_summary(messages_to_summarize)
    
    # 3. 요약 저장
    session.summary = new_summary
    db.session.commit()

# 4. API 호출 시 요약 + 최근 메시지 전송
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "system", "content": f"이전 대화 요약:\n{session.summary}"},
    *[{"role": msg.role, "content": msg.content} for msg in recent_messages],
    {"role": "user", "content": user_message}
]
```

### 토큰 계산

```python
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o-mini")
token_count = len(encoding.encode(text))
```

## 디버깅

### Backend 디버깅

```python
# Flask 디버그 모드
export FLASK_ENV=development
python run.py

# 로그 레벨 설정
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend 디버깅

```javascript
// React DevTools 사용
// Chrome Extension 설치

// 콘솔 로그
console.log('Debug:', data)

// 네트워크 요청 확인
// Chrome DevTools > Network 탭
```

## Git 워크플로우

### 브랜치 전략

```
main (프로덕션)
  ↑
develop (스테이징)
  ↑
feature/* (기능 개발)
bugfix/* (버그 수정)
```

### 커밋 메시지 규칙

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드/설정 변경
```

예시:
```bash
git commit -m "feat: Add video scaffolding management page"
git commit -m "fix: Resolve token counting issue in chat service"
```

## 코드 스타일

### Python (PEP 8)

```bash
# Linting
flake8 backend/app

# 자동 포맷팅
black backend/app
```

### JavaScript (ESLint)

```bash
# Linting
cd frontend
npm run lint

# 자동 수정
npm run lint -- --fix
```

## 성능 최적화

### Backend

1. 데이터베이스 쿼리 최적화
   - `joinedload()` 사용
   - 불필요한 컬럼 제외
   - 인덱스 추가

2. 캐싱 (선택사항)
   - Redis 사용
   - Flask-Caching

### Frontend

1. 코드 스플리팅
   ```javascript
   const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
   ```

2. 메모이제이션
   ```javascript
   const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b])
   ```

## 문제 해결

### 자주 발생하는 이슈

1. **CORS 오류**
   - Backend에서 Flask-CORS 설정 확인
   - Frontend에서 올바른 API URL 사용

2. **JWT 토큰 만료**
   - 자동 갱신 로직 구현
   - 또는 토큰 유효기간 연장

3. **데이터베이스 마이그레이션 충돌**
   ```bash
   flask db stamp head
   flask db migrate
   flask db upgrade
   ```

## 추가 리소스

- Flask 문서: https://flask.palletsprojects.com/
- React 문서: https://react.dev/
- SQLAlchemy 문서: https://docs.sqlalchemy.org/
- OpenAI API 문서: https://platform.openai.com/docs

