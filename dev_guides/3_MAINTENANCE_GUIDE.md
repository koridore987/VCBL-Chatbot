# 유지관리 가이드

VCBL Chatbot의 일상적인 관리 작업과 모니터링 방법을 설명합니다.

## 📊 일상 관리 작업

### 1. 사용자 관리

#### 1.1 사용자 목록 확인
```bash
# Cloud Run Job을 통한 사용자 조회
gcloud run jobs create vcbl-list-users \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="python" \
  --args="-c,from app import create_app, db; from app.models.user import User; app = create_app(); app.app_context().push(); users = User.query.all(); print('총 사용자 수:', len(users)); [print(f'ID: {u.id}, 학번: {u.student_id}, 이름: {u.name}, 권한: {u.role}, 활성: {u.is_active}') for u in users]" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-list-users --region=asia-northeast3 --wait
```

#### 1.2 사용자 권한 변경
```bash
# 관리자 계정 생성
gcloud run jobs create vcbl-create-admin \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="flask" \
  --args="create-admin,2024000002,새관리자,password123" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-create-admin --region=asia-northeast3 --wait
```

#### 1.3 사용자 비활성화
```bash
# 사용자 비활성화 (학번으로)
gcloud run jobs create vcbl-deactivate-user \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="python" \
  --args="-c,from app import create_app, db; from app.models.user import User; app = create_app(); app.app_context().push(); user = User.query.filter_by(student_id=2024000002).first(); user.is_active = False; db.session.commit(); print('사용자 비활성화 완료')" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-deactivate-user --region=asia-northeast3 --wait
```

### 2. 비디오 및 스캐폴딩 관리

#### 2.1 비디오 목록 확인
```bash
# 비디오 목록 조회
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://YOUR_SERVICE_URL/api/videos
```

#### 2.2 새 비디오 추가
```bash
# 비디오 추가 (관리자 권한 필요)
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "새 비디오",
    "youtube_id": "dQw4w9WgXcQ",
    "description": "비디오 설명",
    "scaffolding_mode": "question_response"
  }' \
  https://YOUR_SERVICE_URL/api/admin/videos
```

### 3. 프롬프트 템플릿 관리

#### 3.1 프롬프트 목록 확인
```bash
# 프롬프트 목록 조회
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://YOUR_SERVICE_URL/api/admin/prompts
```

#### 3.2 새 프롬프트 추가
```bash
# 프롬프트 추가
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "기본 프롬프트",
    "description": "기본 시스템 프롬프트",
    "prompt_text": "당신은 학습을 도와주는 AI 어시스턴트입니다.",
    "target_role": "user",
    "is_active": true
  }' \
  https://YOUR_SERVICE_URL/api/admin/prompts
```

## 📈 모니터링 방법

### 1. Cloud Console에서 확인

#### 1.1 Cloud Run 모니터링
- **경로**: Cloud Console > Cloud Run > vcbl-chatbot
- **확인 항목**:
  - 요청 수 (Requests)
  - 응답 시간 (Response time)
  - 에러율 (Error rate)
  - 인스턴스 수 (Instances)
  - CPU/메모리 사용률

#### 1.2 Cloud SQL 모니터링
- **경로**: Cloud Console > SQL > vcbl-postgres
- **확인 항목**:
  - 연결 수 (Connections)
  - CPU 사용률 (CPU utilization)
  - 메모리 사용률 (Memory utilization)
  - 스토리지 사용량 (Storage usage)
  - 쿼리 성능 (Query performance)

#### 1.3 Cloud Logging 모니터링
- **경로**: Cloud Console > Logging > Logs Explorer
- **필터링**:
  ```
  resource.type="cloud_run_revision"
  resource.labels.service_name="vcbl-chatbot"
  ```

### 2. 명령어로 모니터링

#### 2.1 서비스 상태 확인
```bash
# 서비스 상태
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 헬스 체크
curl https://YOUR_SERVICE_URL/health

# 준비 상태 체크
curl https://YOUR_SERVICE_URL/readiness
```

#### 2.2 로그 확인
```bash
# 최근 로그 (50개)
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=50

# 에러 로그만
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="severity>=ERROR" --limit=20

# 실시간 로그 스트리밍
gcloud run services logs tail vcbl-chatbot --region=asia-northeast3

# 특정 시간대 로그
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 \
  --filter="timestamp>=\"2024-01-01T00:00:00Z\"" --limit=100
```

#### 2.3 데이터베이스 상태 확인
```bash
# 데이터베이스 연결 테스트
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

### 3. OpenAI 비용 모니터링

#### 3.1 토큰 사용량 확인
```bash
# 사용자별 토큰 사용량 조회
gcloud run jobs create vcbl-token-usage \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:latest \
  --set-cloudsql-instances=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres \
  --set-env-vars="CLOUD_SQL_INSTANCE=YOUR_PROJECT_ID:asia-northeast3:vcbl-postgres,DB_USER=vcbl_user,DB_NAME=vcbl_chatbot,FLASK_ENV=production" \
  --set-secrets="DB_PASSWORD=vcbl-db-password:latest,SECRET_KEY=vcbl-secret-key:latest,JWT_SECRET_KEY=vcbl-jwt-secret-key:latest,OPENAI_API_KEY=vcbl-openai-api-key:latest" \
  --service-account="vcbl-chatbot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --command="python" \
  --args="-c,from app import create_app, db; from app.models.user import User; app = create_app(); app.app_context().push(); users = User.query.all(); [print(f'사용자: {u.student_id}, 일일 사용량: {u.daily_token_usage}, 총 사용량: {u.total_token_usage}') for u in users]" \
  --region=asia-northeast3

gcloud run jobs execute vcbl-token-usage --region=asia-northeast3 --wait
```

#### 3.2 비용 추정
- **gpt-4o-mini**: $0.00015/1K input tokens, $0.0006/1K output tokens
- **일일 제한**: 50,000 토큰 (기본값)
- **예상 비용**: $7.5/일 (최대 사용 시)

## 💾 데이터베이스 관리

### 1. 백업

#### 1.1 자동 백업 확인
```bash
# 백업 설정 확인
gcloud sql instances describe vcbl-postgres

# 백업 목록 확인
gcloud sql backups list --instance=vcbl-postgres
```

#### 1.2 수동 백업 생성
```bash
# 수동 백업 생성
gcloud sql backups create \
  --instance=vcbl-postgres \
  --description="Manual backup $(date +%Y%m%d_%H%M%S)"
```

### 2. 복원

#### 2.1 백업에서 복원
```bash
# 백업 목록 확인
gcloud sql backups list --instance=vcbl-postgres

# 특정 백업으로 복원
gcloud sql backups restore BACKUP_ID \
  --restore-instance=vcbl-postgres
```

### 3. 마이그레이션

#### 3.1 마이그레이션 실행
```bash
# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait
```

#### 3.2 마이그레이션 상태 확인
```bash
# 마이그레이션 Job 상태 확인
gcloud run jobs describe vcbl-chatbot-migrate --region=asia-northeast3

# 마이그레이션 실행 로그
gcloud run jobs executions list --job=vcbl-chatbot-migrate --region=asia-northeast3
```

## 🔄 업데이트 및 재배포

### 1. 코드 변경 후 재배포

#### 1.1 자동 배포 (GitHub 연동 시)
```bash
# 코드 변경 후 Git에 푸시
git add .
git commit -m "Update: 새로운 기능 추가"
git push origin main
# Cloud Build가 자동으로 배포 실행
```

#### 1.2 수동 배포
```bash
# 빌드 및 배포
gcloud builds submit --config cloudbuild.yaml

# 배포 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3
```

### 2. 데이터베이스 마이그레이션이 필요한 경우

#### 2.1 마이그레이션 파일 생성 (로컬)
```bash
# 로컬에서 마이그레이션 파일 생성
cd backend
source venv/bin/activate
flask db migrate -m "Add new table"
flask db upgrade
```

#### 2.2 마이그레이션 파일을 Git에 푸시
```bash
git add backend/migrations/versions/
git commit -m "Add migration: Add new table"
git push origin main
```

#### 2.3 Cloud에서 마이그레이션 실행
```bash
# 마이그레이션 실행
gcloud run jobs execute vcbl-chatbot-migrate --region=asia-northeast3 --wait
```

### 3. 롤백

#### 3.1 이전 버전으로 롤백
```bash
# 이전 이미지로 롤백
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --image=gcr.io/YOUR_PROJECT_ID/vcbl-chatbot:PREVIOUS_COMMIT_SHA
```

#### 3.2 롤백 확인
```bash
# 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 헬스 체크
curl https://YOUR_SERVICE_URL/health
```

## ⚡ 성능 최적화

### 1. Cloud Run 설정 조정

#### 1.1 리소스 조정
```bash
# CPU/메모리 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --memory=4Gi \
  --cpu=2
```

#### 1.2 스케일링 설정
```bash
# 최소/최대 인스턴스 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --min-instances=2 \
  --max-instances=20
```

### 2. Cloud SQL 최적화

#### 2.1 인스턴스 업그레이드
```bash
# 인스턴스 타입 업그레이드
gcloud sql instances patch vcbl-postgres \
  --tier=db-g1-small
```

#### 2.2 연결 풀 설정 확인
- **현재 설정**: pool_size=5, max_overflow=10 (총 15개)
- **권장**: Cloud SQL 인스턴스 제한의 60% 이하

### 3. 모니터링 설정

#### 3.1 알림 설정
```bash
# Cloud Monitoring에서 알림 정책 생성
# - CPU 사용률 > 80%
# - 메모리 사용률 > 80%
# - 에러율 > 5%
# - 응답 시간 > 1초
```

## 📊 정기 점검 체크리스트

### 일일 점검
- [ ] 서비스 상태 확인 (`/health`, `/readiness`)
- [ ] 에러 로그 확인
- [ ] OpenAI 토큰 사용량 확인
- [ ] 데이터베이스 연결 상태 확인

### 주간 점검
- [ ] 사용자 수 및 활동 확인
- [ ] 비용 사용량 확인
- [ ] 백업 상태 확인
- [ ] 보안 로그 검토

### 월간 점검
- [ ] 성능 메트릭 분석
- [ ] 비용 최적화 검토
- [ ] 보안 업데이트 확인
- [ ] 데이터베이스 정리

## 🚨 응급 상황 대응

### 1. 서비스 다운
```bash
# 1. 서비스 상태 확인
gcloud run services describe vcbl-chatbot --region=asia-northeast3

# 2. 로그 확인
gcloud run services logs read vcbl-chatbot --region=asia-northeast3 --limit=50

# 3. 서비스 재시작
gcloud run services update vcbl-chatbot --region=asia-northeast3
```

### 2. 데이터베이스 연결 실패
```bash
# 1. Cloud SQL 상태 확인
gcloud sql instances describe vcbl-postgres

# 2. 연결 테스트
gcloud sql connect vcbl-postgres --user=vcbl_user --database=vcbl_chatbot

# 3. 인스턴스 재시작 (필요시)
gcloud sql instances restart vcbl-postgres
```

### 3. OpenAI API 오류
```bash
# 1. API 키 확인
gcloud secrets versions access latest --secret="vcbl-openai-api-key"

# 2. 할당량 확인
# OpenAI Platform에서 확인

# 3. 임시 해결책: 토큰 제한 조정
gcloud run services update vcbl-chatbot \
  --region=asia-northeast3 \
  --set-env-vars="DAILY_TOKEN_LIMIT=10000"
```
