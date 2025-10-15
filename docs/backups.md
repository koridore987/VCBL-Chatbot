# 백업 전략 가이드 (Cloud SQL - PostgreSQL)

## 목표
- 비용을 최소화하면서도 위험 구간(배포/행사)에는 안전하게 복구 가능하도록 합니다.

## 전략 요약
- 평상시: 자동 백업/PITR OFF로 비용 최소화 가능 (조직 정책에 따라 조정)
- 위험 구간 직전(배포/행사): 스냅샷 백업 1회 필수 + 필요하면 해당 기간만 PITR ON
- 종료 후: PITR OFF로 원복

## 온디맨드(수동) 스냅샷 백업
```bash
gcloud sql backups create --instance=vcbl-db \
  --description="manual-$(date +%Y%m%d-%H%M%S)"

gcloud sql backups list --instance=vcbl-db --limit=5
```

## 논리 백업(SQL 덤프)
```bash
# GCS 버킷이 있을 때 권장
gcloud sql export sql vcbl-db gs://<버킷>/vcbl_chatbot-$(date +%F).sql.gz \
  --database=vcbl_chatbot --offload
```

## PITR(시점 복구) 기간 한정 활성화
```bash
# 예: 행사 기간 3일만 PITR ON
gcloud sql instances patch vcbl-db \
  --enable-point-in-time-recovery \
  --retained-transaction-log-days=3

# 종료 후 OFF
gcloud sql instances patch vcbl-db --no-enable-point-in-time-recovery
```

## 자동 백업 설정/해제 (선택)
```bash
# 특정 시간대 설정 예시
gcloud sql instances patch vcbl-db --backup-start-time=03:00

# 비활성화
gcloud sql instances patch vcbl-db --no-backup-start-time
```

## 배포 전 백업을 파이프라인에 추가
Cloud Build 예시(배포 단계 전에 배치):
```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: bash
  args:
    - -c
    - |
      set -e
      echo "Creating pre-deploy backup..."
      gcloud sql backups create --instance "${_CLOUD_SQL_INSTANCE_NAME}" \
        --description "pre-deploy-$COMMIT_SHA"
```

`scripts/deploy-unified.sh`에서도 배포 직전에 동일 명령을 추가할 수 있습니다.

## 복구 권장 절차(요약)
1) 새 Cloud SQL 인스턴스로 스냅샷/PITR 복구
2) 애플리케이션을 임시로 해당 인스턴스에 연결해 데이터 확인
3) 이상 없으면 트래픽 스위치 또는 데이터 마이그레이션
