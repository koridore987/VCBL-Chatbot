# 로컬 개발 가이드

이 폴더는 **로컬 개발 환경**에서만 사용되는 파일들을 포함합니다.

## 📁 파일 설명

### `start-local.sh`
로컬에서 백엔드와 프론트엔드를 동시에 실행하는 스크립트입니다.

**사용법:**
```bash
# 프로젝트 루트에서 실행
./dev/start-local.sh
```

**요구사항:**
- `backend/.env` 파일이 설정되어 있어야 합니다
- `frontend/.env` 파일이 설정되어 있어야 합니다
- 백엔드 가상환경(`backend/venv`)이 생성되어 있어야 합니다

### `.env.local` (예시)
로컬 개발용 환경 변수 템플릿입니다.

## 🚀 빠른 시작

1. **초기 설정**
   ```bash
   # 의존성 설치
   ./scripts/setup.sh
   
   # .env 파일 생성
   cp backend/env.example backend/.env
   cp frontend/env.example frontend/.env
   
   # .env 파일을 편집하여 필요한 값 설정
   # 특히 SECRET_KEY와 OPENAI_API_KEY 필수!
   ```

2. **데이터베이스 마이그레이션**
   ```bash
   cd backend
   source venv/bin/activate
   flask db upgrade
   cd ..
   ```

3. **관리자 계정 생성**
   ```bash
   ./scripts/create-admin.sh
   ```

4. **개발 서버 실행**
   ```bash
   ./dev/start-local.sh
   ```

## 📝 노트

- 이 폴더의 파일들은 `.gitignore`에 포함되어 있지 않습니다
- 배포 시에는 이 폴더를 사용하지 않습니다
- 로그 파일(`backend.log`, `frontend.log`)은 `.gitignore`에 포함되어 있습니다

