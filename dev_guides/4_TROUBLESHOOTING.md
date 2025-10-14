# 문제 해결 가이드

VCBL Chatbot 운영 중 발생할 수 있는 문제들과 해결 방법을 설명합니다.

## 🚨 배포 실패

### 1. Cloud Build 오류

#### 1.1 이미지 빌드 실패
**증상**: Cloud Build에서 Docker 이미지 빌드 실패
```
ERROR: failed to build: failed to solve: process "/bin/sh -c pip install" did not complete successfully
```

**해결 방법**:
```bash
# 1. 빌드 로그 확인
gcloud builds log --stream

# 2. 로컬에서 빌드 테스트
docker build -t test-image .

# 3. requirements.txt 확인
cat backend/requirements.txt

# 4. 의존성 문제 해결 후 재빌드
gcloud builds submit --config cloudbuild.yaml
```

#### 1.2 Secret 접근 권한 문제
**증상**: Secret Manager 접근 실패
```
ERROR: Secret [vcbl-secret-key] not found or access denied
```

**해결 방법**:
```bash
# 1. Secret 존재 확인
gcloud secrets list

# 2. 서비스 계정 권한 확인
gcloud projects get-iam-policy YOUR_PROJECT_ID

# 3. Secret Manager 권한 부여
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 4. Secret 재생성 (필요시)
echo -n "new-secret-key" | gcloud secrets create vcbl-secret-key --data-file=-
```

### 2. Cloud Run 배포 실패

#### 2.1 컨테이너 시작 실패
**증상**: Cloud Run 서비스가 시작되지 않음
```
Container failed to start and listen on port 8080
```

**해결 방법**:
```bash
# 1. 서비스 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3

# 2. 환경 변수 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 3. 필수 환경 변수 설정 확인
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="FLASK_ENV=production"

# 4. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

#### 2.2 헬스 체크 실패
**증상**: Cloud Run 헬스 체크 실패
```
Health check failed: HTTP 503
```

**해결 방법**:
```bash
# 1. 헬스 체크 엔드포인트 확인
curl https://YOUR_SERVICE_URL/health
curl https://YOUR_SERVICE_URL/readiness

# 2. 데이터베이스 연결 확인
gcloud run jobs create vcbl-check-db \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="flask" \
  --args="check-db" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-check-db --region=asia-northeast3 --wait
```

## 🔧 런타임 오류

### 1. 데이터베이스 연결 실패

#### 1.1 Cloud SQL 연결 실패
**증상**: 데이터베이스 연결 오류
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**해결 방법**:
```bash
# 1. Cloud SQL 인스턴스 상태 확인
gcloud sql instances describe vcbl-postgres

# 2. 인스턴스가 실행 중인지 확인
gcloud sql instances list

# 3. 인스턴스 시작 (중지된 경우)
gcloud sql instances start vcbl-postgres

# 4. 연결 테스트
gcloud sql connect vcbl-postgres --user=vcbl_user --database=vcbl_chatbot

# 5. 연결 풀 설정 확인
# Cloud Run 서비스의 환경 변수에서 CLOUD_SQL_INSTANCE 확인
```

#### 1.2 연결 수 초과
**증상**: 데이터베이스 연결 수 제한 초과
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) too many connections
```

**해결 방법**:
```bash
# 1. 현재 연결 수 확인
gcloud sql instances describe vcbl-postgres

# 2. 연결 풀 설정 조정 (config.py에서)
# pool_size=3, max_overflow=5 (총 8개로 감소)

# 3. Cloud Run 인스턴스 수 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --max-instances=5

# 4. Cloud SQL 인스턴스 업그레이드 (필요시)
gcloud sql instances patch vcbl-postgres --tier=db-g1-small
```

### 2. OpenAI API 오류

#### 2.1 API 키 오류
**증상**: OpenAI API 인증 실패
```
openai.AuthenticationError: Incorrect API key provided
```

**해결 방법**:
```bash
# 1. API 키 확인
gcloud secrets versions access latest --secret="vcbl-openai-api-key"

# 2. API 키 재설정
echo -n "sk-new-api-key" | gcloud secrets versions add vcbl-openai-api-key --data-file=-

# 3. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

#### 2.2 할당량 초과
**증상**: OpenAI API 할당량 초과
```
openai.RateLimitError: You have exceeded your current quota
```

**해결 방법**:
```bash
# 1. 일일 토큰 제한 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="DAILY_TOKEN_LIMIT=10000"

# 2. OpenAI Platform에서 할당량 확인
# https://platform.openai.com/usage

# 3. 결제 정보 확인
# OpenAI Platform에서 결제 방법 확인
```

#### 2.3 모델 접근 오류
**증상**: 모델 접근 권한 없음
```
openai.PermissionError: The model does not exist or you do not have access to it
```

**해결 방법**:
```bash
# 1. 모델 이름 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3 \
  --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"

# 2. 모델 변경 (gpt-4o-mini 권장)
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="MODEL_NAME=gpt-4o-mini"
```

### 3. 인증 오류

#### 3.1 JWT 토큰 오류
**증상**: JWT 토큰 검증 실패
```
jwt.exceptions.InvalidTokenError: Invalid token
```

**해결 방법**:
```bash
# 1. JWT_SECRET_KEY 확인
gcloud secrets versions access latest --secret="vcbl-jwt-secret-key"

# 2. JWT_SECRET_KEY 재생성
JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
echo -n "$JWT_SECRET" | gcloud secrets versions add vcbl-jwt-secret-key --data-file=-

# 3. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

#### 3.2 CORS 오류
**증상**: CORS 정책 위반
```
Access to fetch at 'https://api.example.com' from origin 'https://frontend.example.com' has been blocked by CORS policy
```

**해결 방법**:
```bash
# 1. CORS_ORIGINS 설정 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 2. CORS_ORIGINS 업데이트
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="CORS_ORIGINS=https://your-frontend-domain.com"
```

## ⚡ 성능 문제

### 1. 응답 속도 저하

#### 1.1 데이터베이스 쿼리 최적화
**증상**: API 응답 시간이 1초 이상
```
Response time: 2.5s (normal: <200ms)
```

**해결 방법**:
```bash
# 1. 데이터베이스 인덱스 확인
gcloud run jobs create vcbl-check-indexes \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="python" \
  --args="-c,from app import create_app, db; app = create_app(); app.app_context().push(); result = db.session.execute(db.text('SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname = \\'public\\'')); print('인덱스 목록:'); [print(f'테이블: {r[1]}, 인덱스: {r[2]}') for r in result]" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-check-indexes --region=asia-northeast3 --wait
```

#### 1.2 Cloud Run 리소스 부족
**증상**: CPU/메모리 사용률 높음
```
CPU usage: 95%, Memory usage: 90%
```

**해결 방법**:
```bash
# 1. 리소스 모니터링
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 2. CPU/메모리 증가
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --memory=4Gi \
  --cpu=2

# 3. 인스턴스 수 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --min-instances=2 \
  --max-instances=10
```

### 2. 메모리 부족

#### 2.1 메모리 사용량 확인
**증상**: 메모리 부족으로 인한 크래시
```
Container killed due to memory limit
```

**해결 방법**:
```bash
# 1. 메모리 사용량 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="severity>=WARNING" --limit=20

# 2. 메모리 증가
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --memory=4Gi

# 3. 연결 풀 크기 조정
# config.py에서 pool_size, max_overflow 감소
```

## 📊 로그 분석

### 1. 로그 확인 방법

#### 1.1 Cloud Console에서 로그 확인
1. **경로**: Cloud Console > Logging > Logs Explorer
2. **필터 설정**:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="vcbl-chatbot"
   severity>=ERROR
   ```

#### 1.2 명령어로 로그 확인
```bash
# 에러 로그만
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="severity>=ERROR" --limit=20

# 특정 시간대 로그
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="timestamp>=\"2024-01-01T00:00:00Z\" AND timestamp<=\"2024-01-01T23:59:59Z\""

# 실시간 로그 스트리밍
gcloud run services logs tail vcbl-chatbot --region=asia-northeast3
```

### 2. 로그 해석

#### 2.1 일반적인 로그 패턴
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "severity": "ERROR",
  "message": "Database connection failed",
  "request_id": "abc123",
  "user": {
    "id": 1,
    "student_id": 2024000001,
    "role": "admin"
  },
  "http": {
    "method": "POST",
    "url": "https://api.example.com/chat",
    "remote_addr": "192.168.1.1"
  }
}
```

#### 2.2 에러 로그 분석
- **severity**: ERROR, WARNING, INFO, DEBUG
- **request_id**: 요청 추적용 고유 ID
- **user**: 사용자 정보 (인증된 경우)
- **http**: HTTP 요청 정보
- **exception**: 예외 정보 (에러 발생 시)

### 3. 성능 로그 분석

#### 3.1 응답 시간 분석
```bash
# 응답 시간이 1초 이상인 요청
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="jsonPayload.duration_ms>1000" --limit=10
```

#### 3.2 데이터베이스 쿼리 분석
```bash
# 데이터베이스 관련 로그
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="jsonPayload.message:\"database\"" --limit=10
```

## 🔍 진단 도구

### 1. 헬스 체크 도구

#### 1.1 기본 헬스 체크
```bash
# 서비스 상태 확인
curl https://YOUR_SERVICE_URL/health

# 준비 상태 확인
curl https://YOUR_SERVICE_URL/readiness
```

#### 1.2 상세 진단
```bash
# 데이터베이스 연결 테스트
gcloud run jobs create vcbl-diagnose \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="flask" \
  --args="check-db" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-diagnose --region=asia-northeast3 --wait
```

### 2. 성능 모니터링

#### 2.1 메트릭 확인
```bash
# Cloud Run 메트릭
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# Cloud SQL 메트릭
gcloud sql instances describe vcbl-postgres
```

#### 2.2 리소스 사용량 확인
```bash
# CPU/메모리 사용률 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="jsonPayload.message:\"resource\"" --limit=10
```

## 🚨 응급 복구

### 1. 서비스 완전 중단 시

#### 1.1 즉시 조치
```bash
# 1. 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 2. 최근 배포로 롤백
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:PREVIOUS_COMMIT_SHA

# 3. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

#### 1.2 데이터베이스 문제 시
```bash
# 1. Cloud SQL 상태 확인
gcloud sql instances describe vcbl-postgres

# 2. 인스턴스 재시작
gcloud sql instances restart vcbl-postgres

# 3. 백업에서 복원 (필요시)
gcloud sql backups list --instance=vcbl-postgres
gcloud sql backups restore BACKUP_ID --restore-instance=vcbl-postgres
```

### 2. 데이터 손실 방지

#### 2.1 즉시 백업 생성
```bash
# 수동 백업 생성
gcloud sql backups create \
  --instance=vcbl-postgres \
  --description="Emergency backup $(date +%Y%m%d_%H%M%S)"
```

#### 2.2 서비스 제한
```bash
# 토큰 제한으로 사용량 제한
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="DAILY_TOKEN_LIMIT=1000"
```

## 📞 지원 요청

### 1. 문제 보고 시 포함할 정보

#### 1.1 필수 정보
- **발생 시간**: 정확한 시간 (UTC)
- **에러 메시지**: 전체 에러 메시지
- **사용자 정보**: 영향받은 사용자 수
- **재현 단계**: 문제 재현 방법

#### 1.2 로그 정보
```bash
# 에러 로그 수집
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="severity>=ERROR" --limit=50 > error_logs.txt

# 서비스 상태 정보
gcloud run services describe vcbl-chatbot --region=asia-northeast3 > service_status.txt
```

### 2. 자주 묻는 질문

#### Q: 서비스가 응답하지 않습니다
A: 
1. `/health` 엔드포인트 확인
2. Cloud Run 서비스 상태 확인
3. 로그에서 에러 메시지 확인
4. 데이터베이스 연결 상태 확인

#### Q: OpenAI API 호출이 실패합니다
A:
1. API 키 유효성 확인
2. 할당량 확인
3. 모델 접근 권한 확인
4. 네트워크 연결 상태 확인

#### Q: 데이터베이스 연결이 실패합니다
A:
1. Cloud SQL 인스턴스 상태 확인
2. 연결 수 제한 확인
3. 방화벽 규칙 확인
4. 서비스 계정 권한 확인
