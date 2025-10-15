# 예약 백업 설정 가이드 (Cloud Run Job + Cloud Scheduler)

## 개요
- Cloud Run Job이 `gcloud sql backups create`를 실행해 스냅샷 백업을 생성합니다.
- Cloud Scheduler가 특정 날짜/시간에 Job 실행 API를 호출합니다.

## 준비 사항
- gcloud 로그인/프로젝트/리전 설정
- 권한
  - 백업 실행용 서비스 계정: `roles/cloudsql.admin`
  - 스케줄러 호출용 서비스 계정: `roles/run.invoker`

## 1) Cloud Run Job 생성/업데이트
```bash
PROJECT_ID=<프로젝트ID>
REGION=asia-northeast3
SQL_INSTANCE=vcbl-db

JOB_SA="vcbl-backup-sa@$PROJECT_ID.iam.gserviceaccount.com"
gcloud iam service-accounts create vcbl-backup-sa --project "$PROJECT_ID" || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$JOB_SA" \
  --role="roles/cloudsql.admin"

if gcloud run jobs describe vcbl-backup-job --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud run jobs update vcbl-backup-job \
    --image=gcr.io/google.com/cloudsdktool/cloud-sdk \
    --region="$REGION" \
    --service-account="$JOB_SA" \
    --command=bash \
    --args=-c,"gcloud sql backups create --instance='$SQL_INSTANCE' --description='scheduled-$(date +%Y%m%d-%H%M%S)'" \
    --project="$PROJECT_ID"
else
  gcloud run jobs create vcbl-backup-job \
    --image=gcr.io/google.com/cloudsdktool/cloud-sdk \
    --region="$REGION" \
    --service-account="$JOB_SA" \
    --command=bash \
    --args=-c,"gcloud sql backups create --instance='$SQL_INSTANCE' --description='scheduled-$(date +%Y%m%d-%H%M%S)'" \
    --project="$PROJECT_ID"
fi
```

## 2) 특정 날짜/시간 1회 실행 스케줄러 생성
예: 2025-11-10 23:55 (KST)
```bash
PROJECT_ID=<프로젝트ID>
REGION=asia-northeast3
TIMEZONE="Asia/Seoul"
SCHEDULE="55 23 10 11 *"  # 11월 10일 23:55

SCHEDULER_SA="vcbl-scheduler-sa@$PROJECT_ID.iam.gserviceaccount.com"
gcloud iam service-accounts create vcbl-scheduler-sa --project "$PROJECT_ID" || true

gcloud run jobs add-iam-policy-binding vcbl-backup-job \
  --region="$REGION" \
  --member="serviceAccount:$SCHEDULER_SA" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID"

RUN_URL="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/vcbl-backup-job:run"

gcloud scheduler jobs create http backup-once-20251110-2355 \
  --location="$REGION" \
  --schedule="$SCHEDULE" \
  --time-zone="$TIMEZONE" \
  --http-method=POST \
  --uri="$RUN_URL" \
  --oauth-service-account-email="$SCHEDULER_SA" \
  --oauth-token-audience="https://$REGION-run.googleapis.com/" \
  --project="$PROJECT_ID"
```

## 3) 즉시 수동 실행(테스트)
```bash
gcloud run jobs execute vcbl-backup-job --region "$REGION" --project "$PROJECT_ID"
```

## 참고
- 날짜가 여러 개면 2)만 복제하여 이름/크론식만 변경하세요.
- 조직 정책에 따라 Cloud Scheduler `--location`은 Cloud Run 리전과 다를 수 있습니다(예: `us-central1`).
