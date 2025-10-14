# 환경 변수 가이드

VCBL Chatbot의 모든 환경 변수에 대한 상세한 설명입니다.

## 🔐 Secret Manager 변수 (민감 정보)

이 변수들은 Google Cloud Secret Manager에 저장되어 보안이 강화됩니다.

| Secret 이름 | 설명 | 생성 방법 | 예시 |
|------------|------|----------|------|
| `vcbl-secret-key` | Flask 세션 암호화 키 | `python -c "import secrets; print(secrets.token_hex(32))"` | `a1b2c3d4e5f6...` |
| `vcbl-jwt-secret-key` | JWT 토큰 서명 키 | `python -c "import secrets; print(secrets.token_hex(32))"` | `e5f6g7h8i9j0...` |
| `vcbl-db-password` | PostgreSQL 데이터베이스 비밀번호 | Cloud SQL 사용자 생성 시 설정 | `your_secure_password` |
| `vcbl-openai-api-key` | OpenAI API 키 | OpenAI 플랫폼에서 발급 | `sk-proj-...` |
| `vcbl-redis-url` | Redis 연결 URL (선택) | 외부 Redis 사용 시 설정 | `redis://host:port` |
| `vcbl-super-admin-id` | 초기 super admin 학번 | 원하는 학번 (10자리 정수) | `2024000001` |
| `vcbl-super-admin-name` | 초기 super admin 이름 | 관리자 표시 이름 | `관리자` |
| `vcbl-super-admin-password` | 초기 super admin 비밀번호 | 최소 8자, 복잡한 비밀번호 권장 | `SecurePass123!` |

### Secret Manager 설정 방법

```bash
# SECRET_KEY 생성 및 저장
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
echo -n "$SECRET_KEY" | gcloud secrets create vcbl-secret-key --data-file=-

# JWT_SECRET_KEY 생성 및 저장
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
echo -n "$JWT_SECRET_KEY" | gcloud secrets create vcbl-jwt-secret-key --data-file=-

# 데이터베이스 비밀번호 저장
echo -n "your_secure_password" | gcloud secrets create vcbl-db-password --data-file=-

# OpenAI API 키 저장
echo -n "sk-your-openai-api-key" | gcloud secrets create vcbl-openai-api-key --data-file=-

# Redis URL 저장 (선택)
echo -n "memory://" | gcloud secrets create vcbl-redis-url --data-file=-

# Super admin 정보 저장
echo -n "2024000001" | gcloud secrets create vcbl-super-admin-id --data-file=-
echo -n "관리자" | gcloud secrets create vcbl-super-admin-name --data-file=-
echo -n "SecurePass123!" | gcloud secrets create vcbl-super-admin-password --data-file=-
```

## 🌐 Cloud Run 환경 변수 (일반 설정)

이 변수들은 Cloud Run 서비스에 직접 설정됩니다.

| 변수 이름 | 설명 | 기본값 | 권장값 | 필수 |
|----------|------|--------|--------|------|
| `FLASK_ENV` | Flask 환경 모드 | `development` | `production` | ✅ |
| `CLOUD_SQL_INSTANCE` | Cloud SQL 연결 이름 | - | `project-id:region:instance-name` | ✅ |
| `DB_USER` | 데이터베이스 사용자명 | - | `vcbl_user` | ✅ |
| `DB_NAME` | 데이터베이스 이름 | - | `vcbl_chatbot` | ✅ |
| `PORT` | 서버 포트 | `8080` | `8080` | ❌ |
| `CORS_ORIGINS` | 허용할 Origin | `http://localhost:5173` | `https://your-domain.com` | ❌ |
| `MODEL_NAME` | OpenAI 모델 | `gpt-4o-mini` | `gpt-4o-mini` | ❌ |
| `SUMMARY_TRIGGER_TOKENS` | 요약 트리거 토큰 수 | `3500` | `3500` | ❌ |
| `MAX_TOKENS_PER_REQUEST` | 요청당 최대 토큰 | `4000` | `4000` | ❌ |
| `MAX_TOKENS_OUTPUT` | 응답 최대 토큰 | `1000` | `1000` | ❌ |
| `DAILY_TOKEN_LIMIT` | 일일 토큰 제한 | `50000` | `50000` | ❌ |
| `WORKERS` | Gunicorn worker 수 | 자동 계산 | `4` | ❌ |

### Cloud Run 환경 변수 설정 방법

```bash
# 환경 변수 설정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="FLASK_ENV=production,CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,CORS_ORIGINS=https://your-domain.com"
```

## 💻 Local 개발 환경 변수

로컬 개발 시 사용하는 환경 변수입니다.

### backend/.env 파일
```bash
# Flask 환경
FLASK_ENV=development
PORT=8080

# 보안 설정
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-min-32-chars

# 데이터베이스 설정 (PostgreSQL 권장)
DATABASE_URL=postgresql://vcbl_user:vcbl_dev_password@localhost:5432/vcbl_chatbot

# OpenAI 설정
OPENAI_API_KEY=sk-your-openai-api-key-here
MODEL_NAME=gpt-4o-mini

# CORS 설정
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Rate Limiting
REDIS_URL=redis://redis:6379/0
```

### frontend/.env 파일
```bash
# API 백엔드 URL
VITE_API_URL=http://localhost:8080/api
```

## 🔧 환경별 설정 차이점

### Development (로컬 개발)
- **데이터베이스**: SQLite (기본) 또는 PostgreSQL (권장)
- **로깅**: 사람이 읽기 쉬운 형태
- **Rate Limiting**: 비활성화
- **CORS**: localhost 허용
- **디버그**: 활성화

### Production (Cloud Run)
- **데이터베이스**: Cloud SQL PostgreSQL
- **로깅**: JSON 형태 (Cloud Logging 최적화)
- **Rate Limiting**: 활성화
- **CORS**: 지정된 도메인만 허용
- **디버그**: 비활성화

## 📊 변수별 상세 설명

### 보안 관련

#### SECRET_KEY
- **용도**: Flask 세션, 쿠키 암호화
- **길이**: 최소 32자 권장
- **보안**: 절대 노출 금지, 정기적 변경 권장
- **생성**: `python -c "import secrets; print(secrets.token_hex(32))"`

#### JWT_SECRET_KEY
- **용도**: JWT 토큰 서명/검증
- **길이**: 최소 32자 권장
- **보안**: 노출 시 모든 토큰 무효화 필요
- **생성**: `python -c "import secrets; print(secrets.token_hex(32))"`

### 데이터베이스 관련

#### CLOUD_SQL_INSTANCE
- **형식**: `프로젝트ID:리전:인스턴스명`
- **예시**: `my-project:asia-northeast3:vcbl-postgres`
- **용도**: Cloud SQL Unix socket 연결

#### DATABASE_URL (로컬 개발)
- **PostgreSQL**: `postgresql://user:password@host:port/database`
- **SQLite**: `sqlite:///filename.db`
- **용도**: SQLAlchemy 연결 문자열

### OpenAI 관련

#### OPENAI_API_KEY
- **형식**: `sk-`로 시작하는 51자 문자열
- **용도**: OpenAI API 인증
- **보안**: 비용 발생하므로 철저히 보호
- **발급**: [OpenAI Platform](https://platform.openai.com/api-keys)

#### MODEL_NAME
- **기본값**: `gpt-4o-mini` (가장 저렴)
- **옵션**: `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`
- **비용**: 모델별로 토큰당 요금 차이

#### 토큰 제한 설정
- **SUMMARY_TRIGGER_TOKENS**: 대화가 이 토큰 수를 초과하면 요약 생성
- **MAX_TOKENS_PER_REQUEST**: 요청당 최대 토큰 수
- **MAX_TOKENS_OUTPUT**: 응답 최대 토큰 수
- **DAILY_TOKEN_LIMIT**: 사용자당 하루 토큰 사용 제한

### 운영 관련

#### CORS_ORIGINS
- **개발**: `http://localhost:5173,http://localhost:3000`
- **프로덕션**: `https://your-domain.com,https://www.your-domain.com`
- **보안**: 허용할 도메인만 명시

#### REDIS_URL
- **로컬**: `redis://redis:6379/0` (Docker Compose)
- **프로덕션**: `memory://` (기본) 또는 외부 Redis
- **용도**: Rate limiting 저장소

#### WORKERS
- **계산**: CPU 코어 수 × 2 + 1
- **권장**: 4-8개
- **용도**: Gunicorn worker 프로세스 수

## ⚠️ 주의사항

### 보안
1. **Secret Manager 변수는 절대 코드에 하드코딩하지 마세요**
2. **SECRET_KEY와 JWT_SECRET_KEY는 정기적으로 변경하세요**
3. **OpenAI API 키는 비용 발생하므로 철저히 보호하세요**
4. **데이터베이스 비밀번호는 복잡하게 설정하세요**

### 성능
1. **Cloud SQL 연결 수 제한을 고려하세요** (f1-micro: 25개)
2. **토큰 제한을 적절히 설정하여 비용을 관리하세요**
3. **CORS_ORIGINS를 필요한 도메인만 허용하세요**

### 개발
1. **로컬 개발 시 PostgreSQL 사용을 권장합니다**
2. **환경 변수 변경 후 애플리케이션을 재시작하세요**
3. **프로덕션 배포 전 모든 환경 변수를 확인하세요**

## 🔄 환경 변수 업데이트

### Cloud Run 서비스 업데이트
```bash
# 환경 변수 업데이트
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="NEW_VAR=value"

# Secret 업데이트
gcloud secrets versions add vcbl-secret-key --data-file=-
```

### 로컬 개발 환경 업데이트
```bash
# .env 파일 수정 후
# 백엔드 재시작
cd backend
source venv/bin/activate
python run.py

# 프론트엔드 재시작
cd frontend
npm run dev
```
