# 로컬 개발 환경 설정 가이드

이 가이드는 VCBL Chatbot을 로컬 환경에서 개발하기 위한 설정 방법을 설명합니다.

## 📋 개발 환경 옵션

### 옵션 1: Docker Compose (권장 ⭐)

**장점:**
- 프로덕션 환경(PostgreSQL)과 동일한 데이터베이스 사용
- 간단한 설정
- 전체 스택 통합 테스트 가능

**단점:**
- Docker 필요
- 약간 느린 시작 시간

### 옵션 2: 로컬 Python + SQLite

**장점:**
- 빠른 시작
- Docker 불필요
- 가벼움

**단점:**
- SQLite와 PostgreSQL 동작 차이
- 프로덕션과 다른 환경

---

## 🚀 옵션 1: Docker Compose 개발 환경 (권장)

### 1단계: 사전 준비

```bash
# Docker 및 Docker Compose 설치 확인
docker --version
docker-compose --version
```

### 2단계: 환경 변수 설정

```bash
# backend/.env 파일 생성
cd backend
cp env.example .env

# .env 파일 편집
# 최소한 다음 항목 설정:
# - OPENAI_API_KEY=sk-your-key
# - SECRET_KEY=<생성된 키>
# - JWT_SECRET_KEY=<생성된 키>
```

**키 생성:**
```bash
# SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))"

# JWT_SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3단계: 컨테이너 시작

```bash
# 프로젝트 루트에서
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

### 4단계: 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
docker-compose exec app flask db upgrade
```

### 5단계: Super Admin 생성

```bash
# 기본 계정으로 생성 (super / super1234)
docker-compose exec app flask init-admin

# 또는 커스텀 정보로 생성
docker-compose exec app flask init-admin \
  --student-id 2024000001 \
  --name "관리자" \
  --password "YourPassword123!"
```

### 6단계: 접속

- **웹 애플리케이션**: http://localhost:8080
- **API**: http://localhost:8080/api
- **PostgreSQL**: localhost:5432
  - 사용자: `vcbl_user`
  - 비밀번호: `vcbl_dev_password`
  - 데이터베이스: `vcbl_chatbot`

### 일반적인 작업

```bash
# 컨테이너 중지
docker-compose down

# 데이터 완전 삭제 (주의!)
docker-compose down -v

# 컨테이너 재시작
docker-compose restart app

# 로그 확인
docker-compose logs -f

# Flask 명령 실행
docker-compose exec app flask <command>

# 셸 접속
docker-compose exec app bash
```

---

## 🐍 옵션 2: 로컬 Python 개발 환경

### 1단계: Python 환경 준비

```bash
# Python 3.11 이상 필요
python --version

# 가상 환경 생성
cd backend
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2단계: 의존성 설치

```bash
pip install -r requirements.txt
```

### 3단계: 환경 변수 설정

```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집
# SQLite 사용 (빠른 개발):
DATABASE_URL=sqlite:///vcbl_chatbot.db

# 또는 로컬 PostgreSQL 사용:
# DATABASE_URL=postgresql://user:password@localhost:5432/vcbl_chatbot
```

### 4단계: 데이터베이스 초기화

```bash
# 마이그레이션 실행
flask db upgrade

# Super Admin 생성
flask init-admin
```

### 5단계: 백엔드 서버 시작

```bash
# 개발 서버 시작
python run.py

# 또는 Flask 직접 실행
flask run --port 8080
```

### 6단계: 프론트엔드 개발 서버 (별도 터미널)

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

### 7단계: 접속

- **프론트엔드 (개발 서버)**: http://localhost:5173
- **백엔드 API**: http://localhost:8080/api

---

## 🛠️ 개발 작업

### 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
flask db revision -m "설명"

# 마이그레이션 편집 후 실행
flask db upgrade

# 마이그레이션 되돌리기
flask db downgrade

# 현재 마이그레이션 상태 확인
flask db current
```

### 코드 변경 시

**Docker Compose:**
```bash
# 백엔드 코드 변경 시 재빌드 필요
docker-compose up -d --build app
```

**로컬 Python:**
- 백엔드: 자동 재로드 (Flask debug 모드)
- 프론트엔드: 자동 재로드 (Vite HMR)

### 데이터베이스 초기화

**Docker Compose:**
```bash
# 데이터베이스 볼륨 삭제 및 재시작
docker-compose down -v
docker-compose up -d
docker-compose exec app flask db upgrade
docker-compose exec app flask init-admin
```

**로컬 Python:**
```bash
# SQLite 파일 삭제
rm vcbl_chatbot.db

# 마이그레이션 재실행
flask db upgrade
flask init-admin
```

---

## 🧪 테스트

### 단위 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 파일 테스트
pytest tests/test_auth.py

# 커버리지 포함
pytest --cov=app
```

### API 테스트

```bash
# 헬스 체크
curl http://localhost:8080/health

# 회원가입
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"student_id": "2024000001", "name": "테스트", "password": "test1234"}'

# 로그인
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id": "2024000001", "password": "test1234"}'
```

---

## 🐛 디버깅

### VSCode 디버깅 설정

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "run.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 로그 레벨 조정

`.env`:
```bash
LOG_LEVEL=DEBUG
```

---

## 📊 데이터베이스 관리

### PostgreSQL 접속 (Docker Compose)

```bash
# psql로 접속
docker-compose exec db psql -U vcbl_user -d vcbl_chatbot

# 또는 외부 클라이언트 사용
# Host: localhost
# Port: 5432
# User: vcbl_user
# Password: vcbl_dev_password
# Database: vcbl_chatbot
```

### SQLite 관리 (로컬 Python)

```bash
# SQLite CLI
sqlite3 vcbl_chatbot.db

# 또는 GUI 도구 사용 (DB Browser for SQLite 등)
```

---

## 🔧 문제 해결

### 포트가 이미 사용 중

```bash
# Docker Compose
docker-compose down
# 다른 프로세스가 8080 포트 사용 시 docker-compose.yml에서 포트 변경

# 로컬 Python
# run.py에서 포트 변경 또는 .env에서 PORT 설정
```

### 데이터베이스 연결 실패

**Docker Compose:**
```bash
# 컨테이너 상태 확인
docker-compose ps

# 데이터베이스 로그 확인
docker-compose logs db

# 헬스 체크
docker-compose exec db pg_isready -U vcbl_user
```

**로컬 Python:**
```bash
# DATABASE_URL 확인
echo $DATABASE_URL

# SQLite 파일 권한 확인
ls -la vcbl_chatbot.db
```

### 마이그레이션 오류

```bash
# 마이그레이션 히스토리 확인
flask db history

# 마이그레이션 상태 확인
flask db current

# 강제 스탬프 (주의!)
flask db stamp head
```

---

## 💡 개발 팁

### 1. 환경별 설정

`.env` 파일을 환경별로 관리:
- `.env.development` - 로컬 개발
- `.env.test` - 테스트
- `.env.production` - 프로덕션 (Git 제외)

### 2. 코드 스타일

```bash
# black (포매터)
pip install black
black backend/

# flake8 (린터)
pip install flake8
flake8 backend/
```

### 3. Git Hook 설정

`.git/hooks/pre-commit`:
```bash
#!/bin/bash
black backend/ --check
flake8 backend/
pytest
```

### 4. 빠른 데이터 추가

개발용 더미 데이터:
```python
# backend/seed_data.py
from app import create_app, db
from app.models.user import User
from app.models.video import Video

app = create_app()
with app.app_context():
    # 더미 비디오 추가
    video = Video(title="테스트 비디오", ...)
    db.session.add(video)
    db.session.commit()
```

```bash
python backend/seed_data.py
```

---

## 📚 추가 리소스

- [Flask 문서](https://flask.palletsprojects.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Vite 문서](https://vitejs.dev/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

## ✅ 개발 체크리스트

- [ ] 가상 환경 활성화
- [ ] 의존성 설치 완료
- [ ] 환경 변수 설정 (`.env`)
- [ ] 데이터베이스 마이그레이션 실행
- [ ] Super Admin 계정 생성
- [ ] 백엔드 서버 시작 확인
- [ ] 프론트엔드 서버 시작 확인
- [ ] 로그인 테스트
- [ ] API 응답 확인

---

Happy Coding! 🚀

