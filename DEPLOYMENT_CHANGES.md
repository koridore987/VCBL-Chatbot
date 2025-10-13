# Google Cloud Run 배포 변경 사항

이 문서는 Google Cloud Run과 PostgreSQL을 사용한 프로덕션 배포를 위해 수행된 변경 사항을 요약합니다.

## 변경 날짜
2025년 10월 13일

## 목표
- Google Cloud Run에 배포
- PostgreSQL을 사용한 다중 작업 지원
- Docker를 사용한 컨테이너화
- 자동 스케일링 및 고가용성

---

## 주요 변경 사항

### 1. 백엔드 (Backend)

#### `backend/requirements.txt`
- **추가된 패키지**:
  - `psycopg2-binary==2.9.9` - PostgreSQL 어댑터
  - `pg8000==1.30.3` - 순수 Python PostgreSQL 드라이버
  - `cloud-sql-python-connector[pg8000]==1.5.0` - Cloud SQL 연결자

#### `backend/app/config.py`
- **새로운 함수**: `get_database_url()`
  - Cloud SQL Unix 소켓 연결 지원
  - 환경 변수에 따른 동적 DATABASE_URL 생성
  - SQLite, PostgreSQL, Cloud SQL 모두 지원

- **연결 풀 설정 업데이트**:
  ```python
  SQLALCHEMY_ENGINE_OPTIONS = {
      'pool_pre_ping': True,
      'pool_recycle': 300,
      'pool_size': 10,        # 새로 추가
      'max_overflow': 20,     # 새로 추가
      'pool_timeout': 30,     # 새로 추가
  }
  ```

#### `backend/env.example`
- PostgreSQL 연결 예제 추가
- Cloud SQL 설정 가이드 추가
- Docker Compose 설정 추가
- 상세한 주석 및 설명 추가

---

### 2. 인프라 (Infrastructure)

#### `Dockerfile`
- **변경 사항**:
  - PostgreSQL 클라이언트 라이브러리 추가 (`libpq-dev`, `libpq5`)
  - `postgresql-client` 도구 포함
  - 다중 단계 빌드 유지 (backend-builder, frontend-builder, production)

#### `docker-compose.yml`
- **완전히 재작성**:
  - PostgreSQL 15 서비스 추가
  - Redis 서비스 추가 (Rate Limiting용)
  - 헬스 체크 설정
  - 영구 볼륨 설정
  - 서비스 간 의존성 관리
  - 환경 변수 기본값 설정

#### `cloudbuild.yaml`
- **주요 업데이트**:
  - Cloud SQL 연결 설정 (`--add-cloudsql-instances`)
  - Secret Manager 통합 (`--set-secrets`)
  - 리소스 설정 (2Gi 메모리, 2 CPU)
  - 자동 스케일링 (1~100 인스턴스)
  - 동시성 설정 (인스턴스당 80 요청)
  - 서비스 계정 지정
  - 마이그레이션 Job 실행 단계 추가

---

### 3. 배포 스크립트

#### 새로 생성된 스크립트

**`scripts/start.sh`**
- Nginx 및 Gunicorn 시작 스크립트
- 동적 워커 수 계산
- 프로덕션 환경에서 자동 마이그레이션
- 멀티스레드 워커 설정

**`scripts/deploy-setup.sh`**
- Google Cloud 초기 설정 자동화
- API 활성화
- 서비스 계정 생성 및 권한 부여
- Cloud SQL 인스턴스 생성
- 데이터베이스 및 사용자 생성
- Secret Manager 설정
- 대화형 프롬프트로 사용자 입력

**`scripts/run-migration.sh`**
- Cloud SQL Proxy 가이드
- Cloud Run Jobs를 통한 마이그레이션
- 자동 마이그레이션 Job 생성/업데이트

**`scripts/deploy.sh`**
- 간편한 배포 스크립트
- Cloud Build 트리거
- 배포 후 URL 및 상태 확인

---

### 4. 문서

#### 새로 생성된 문서

**`docs/GOOGLE_CLOUD_DEPLOYMENT.md`**
- 완전한 Google Cloud Run 배포 가이드
- 단계별 상세 지침
- 문제 해결 섹션
- 보안 권장사항
- 비용 최적화 가이드
- CI/CD 파이프라인 설정
- 모니터링 및 로깅

**`QUICKSTART.md`**
- 빠른 시작 가이드
- 로컬 개발 3단계
- Cloud Run 배포 3단계
- 일반적인 문제 해결

**`DEPLOYMENT_CHANGES.md`** (이 파일)
- 변경 사항 요약
- 마이그레이션 가이드

#### 업데이트된 문서

**`README.md`**
- Deployment 섹션 업데이트
- Docker Compose 실행 방법 개선
- Google Cloud Run 배포 섹션 추가
- 배포 아키텍처 다이어그램 추가

**`frontend/env.example`**
- 프로덕션 URL 예제 추가
- 주석 추가

---

## 환경 변수 변경

### 새로운 환경 변수

#### Cloud SQL 관련
- `CLOUD_SQL_INSTANCE` - Cloud SQL 인스턴스 연결 이름
- `DB_USER` - 데이터베이스 사용자
- `DB_PASSWORD` - 데이터베이스 비밀번호
- `DB_NAME` - 데이터베이스 이름

#### 기존 변수 (변경 없음)
- `DATABASE_URL` - 여전히 지원 (우선순위 높음)
- `SECRET_KEY`, `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- 기타 OpenAI 설정

---

## 마이그레이션 가이드

### 기존 SQLite에서 PostgreSQL로 마이그레이션

#### 1. 데이터 백업

```bash
# SQLite 데이터 덤프
sqlite3 vcbl_chatbot.db .dump > backup.sql
```

#### 2. PostgreSQL로 데이터 가져오기

```bash
# Cloud SQL Proxy 시작
./cloud_sql_proxy -instances=PROJECT_ID:asia-northeast3:vcbl-postgres=tcp:5432 &

# pgloader 사용 (권장)
pgloader sqlite:///path/to/vcbl_chatbot.db \
  postgresql://vcbl_user:PASSWORD@localhost:5432/vcbl_chatbot

# 또는 수동 마이그레이션 스크립트 작성
```

#### 3. 데이터 검증

```bash
# PostgreSQL에 연결하여 데이터 확인
psql -h localhost -U vcbl_user -d vcbl_chatbot

# 테이블 및 레코드 수 확인
\dt
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM videos;
SELECT COUNT(*) FROM chat_sessions;
```

---

## 배포 아키텍처

### 이전 (SQLite)

```
┌─────────────────┐
│   Cloud Run     │
│  (Single File)  │
│   + SQLite DB   │
└─────────────────┘
```

**제한사항**:
- 인스턴스 간 데이터 공유 불가
- 스케일링 제한
- 데이터 영속성 문제

### 현재 (PostgreSQL + Cloud SQL)

```
┌─────────────────┐
│   Cloud Build   │ ← GitHub Push
└────────┬────────┘
         │ Build & Deploy
         ▼
┌─────────────────┐      ┌──────────────────┐
│   Cloud Run     │ ───► │  Cloud SQL       │
│  (Auto-scaled)  │      │  (PostgreSQL 15) │
│   1~100 inst.   │      │   High Available │
└─────────────────┘      └──────────────────┘
         │
         │ Secrets
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Secret Manager  │      │  Cloud Logging   │
│   (Secure)      │      │   & Monitoring   │
└─────────────────┘      └──────────────────┘
```

**장점**:
- ✅ 무제한 자동 스케일링 (0~100 인스턴스)
- ✅ 다중 작업 동시 처리
- ✅ 고가용성 및 자동 백업
- ✅ 데이터 일관성 보장
- ✅ 보안 강화 (Secret Manager)

---

## 로컬 개발 환경

### 이전

```bash
# 백엔드만 실행
cd backend
python run.py

# 프론트엔드 별도 실행
cd frontend
npm run dev
```

### 현재

```bash
# 모든 서비스 한 번에 실행
docker-compose up -d

# PostgreSQL + Redis + Backend + Frontend (빌드됨)
# http://localhost:8080 접속
```

---

## 비용 예상

### 소규모 운영 (학생 100명 이하)
- **Cloud Run**: $0-5/월
- **Cloud SQL** (db-f1-micro): $7-10/월
- **네트워크**: $0-2/월
- **총**: ~$10-20/월

### 중규모 운영 (학생 500명)
- **Cloud Run**: $10-30/월
- **Cloud SQL** (db-g1-small): $25-35/월
- **네트워크**: $2-5/월
- **총**: ~$40-70/월

*실제 비용은 사용량에 따라 달라집니다.*

---

## 보안 강화

### 변경된 보안 설정

1. **Secret Manager 사용**
   - 코드에 비밀 키 없음
   - 런타임에 동적으로 로드

2. **IAM 권한 분리**
   - 서비스 계정별 최소 권한
   - Cloud SQL 클라이언트 권한만 부여

3. **연결 암호화**
   - Unix 소켓을 통한 Cloud SQL 연결
   - TLS/SSL 자동 적용

4. **환경 분리**
   - 개발/스테이징/프로덕션 분리
   - 환경별 Secret 관리

---

## 다음 단계

### 권장 사항

1. **CI/CD 설정**
   - GitHub와 Cloud Build 연동
   - 자동 테스트 추가
   - 점진적 배포 (Blue-Green)

2. **모니터링 강화**
   - Cloud Monitoring 대시보드 설정
   - 알림 규칙 생성
   - 로그 기반 메트릭

3. **성능 최적화**
   - CDN 추가 (Cloud CDN)
   - 이미지 최적화
   - 캐싱 전략 개선

4. **백업 자동화**
   - 정기 백업 확인
   - 복구 절차 테스트
   - 백업 보관 정책 설정

---

## 문제 해결

### 일반적인 문제

1. **"Database connection failed"**
   - Cloud SQL 인스턴스 상태 확인
   - 서비스 계정 권한 확인
   - Secret Manager 값 확인

2. **"Container failed to start"**
   - Cloud Build 로그 확인
   - 환경 변수 설정 확인
   - Dockerfile 빌드 로그 확인

3. **"Secret not found"**
   - Secret Manager에 Secret 존재 여부 확인
   - 서비스 계정의 Secret Accessor 권한 확인

자세한 문제 해결은 [Google Cloud Deployment 가이드](docs/GOOGLE_CLOUD_DEPLOYMENT.md#문제-해결)를 참고하세요.

---

## 지원

추가 지원이 필요하면:

- 📖 [Google Cloud Deployment 가이드](docs/GOOGLE_CLOUD_DEPLOYMENT.md)
- 🚀 [빠른 시작 가이드](QUICKSTART.md)
- 📝 [README](README.md)
- 🐛 [GitHub Issues](https://github.com/your-repo/issues)

---

**업데이트 완료! 🎉**

