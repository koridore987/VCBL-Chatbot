# VCBL Chatbot - 단순화 버전

이 버전은 SQLite를 사용하여 복잡성을 줄이고 Google Cloud Run에 쉽게 배포할 수 있도록 단순화되었습니다.

## 🚀 주요 변경사항

### 백엔드 단순화
- ✅ PostgreSQL → SQLite로 변경
- ✅ Flask-Migrate 제거 (자동 테이블 생성)
- ✅ 복잡한 의존성 제거

### 프론트엔드 단순화
- ✅ 불필요한 패키지 제거 (react-youtube, codemirror 등)
- ✅ 핵심 기능만 유지

### 배포 단순화
- ✅ 단일 Docker 컨테이너
- ✅ Google Cloud Run 최적화
- ✅ SQLite 파일 영구 저장

## 📁 프로젝트 구조

```
VCBL-Chatbot/
├── backend/                 # Flask 백엔드
│   ├── app/
│   │   ├── models/         # SQLAlchemy 모델
│   │   ├── routes/         # API 라우트
│   │   └── services/       # 비즈니스 로직
│   ├── requirements.txt    # 단순화된 의존성
│   └── run.py             # 앱 진입점
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/         # 페이지 컴포넌트
│   │   └── services/      # API 서비스
│   └── package.json       # 단순화된 의존성
├── Dockerfile.simple      # 단순화된 Dockerfile
├── docker-compose.simple.yml
├── cloudbuild.yaml        # Google Cloud Build 설정
├── deploy.sh             # 배포 스크립트
└── env.example           # 환경 변수 예시
```

## 🛠️ 로컬 개발

### 1. 환경 설정
```bash
# 백엔드 가상환경 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd ../frontend
npm install
```

### 2. 환경 변수 설정
```bash
# backend/.env 파일 생성
cp env.example backend/.env
# 필요한 값들 수정
```

### 3. 개발 서버 실행
```bash
# 백엔드 실행
cd backend
python run.py

# 프론트엔드 실행 (새 터미널)
cd frontend
npm run dev
```

## 🐳 Docker로 실행

### 단순화된 Docker Compose 사용
```bash
# SQLite 기반으로 실행
docker-compose -f docker-compose.simple.yml up --build
```

## ☁️ Google Cloud Run 배포

### 1. 사전 준비
```bash
# Google Cloud CLI 설치 및 로그인
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Container Registry API 활성화
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
```

### 2. 환경 변수 설정
```bash
# env.example을 참고하여 .env 파일 생성
cp env.example .env
# PROJECT_ID, SECRET_KEY, OPENAI_API_KEY 등 설정
```

### 3. 배포 실행
```bash
# 자동 배포 스크립트 실행
./deploy.sh

# 또는 수동 배포
gcloud builds submit --config cloudbuild.yaml
```

### 4. 배포 확인
```bash
# 서비스 URL 확인
gcloud run services describe vcbl-chatbot --region asia-northeast3 --format 'value(status.url)'
```

## 🔧 주요 설정

### SQLite 데이터베이스
- 로컬: `sqlite:///vcbl_chatbot.db`
- Cloud Run: `sqlite:///app/data/vcbl_chatbot.db`

### 환경 변수
- `DATABASE_URL`: SQLite 데이터베이스 경로
- `SECRET_KEY`: JWT 시크릿 키
- `OPENAI_API_KEY`: OpenAI API 키
- `MODEL_NAME`: 사용할 GPT 모델 (기본: gpt-4o-mini)

## 📊 성능 최적화

### Cloud Run 설정
- **메모리**: 1Gi
- **CPU**: 1
- **최대 인스턴스**: 10
- **포트**: 8080

### SQLite 최적화
- WAL 모드 사용
- 적절한 인덱싱
- 정기적인 VACUUM

## 🚨 주의사항

1. **SQLite 제한사항**
   - 동시 쓰기 제한 (Cloud Run에서는 단일 인스턴스)
   - 백업 필요 (Cloud Storage 연동 권장)

2. **Cloud Run 제한사항**
   - 인스턴스당 1GB 디스크 공간
   - 콜드 스타트 시간 고려

3. **보안**
   - SECRET_KEY는 강력한 값으로 설정
   - OpenAI API 키 보안 관리

## 🔄 마이그레이션 가이드

기존 PostgreSQL 버전에서 이 단순화 버전으로 마이그레이션하려면:

1. 데이터베이스 데이터 내보내기
2. SQLite 스키마에 맞게 데이터 변환
3. 새로운 환경 변수 설정
4. 테스트 후 배포

## 📞 지원

문제가 발생하면 다음을 확인하세요:
- 환경 변수 설정
- Google Cloud 권한
- Docker 이미지 빌드 로그
- Cloud Run 로그
