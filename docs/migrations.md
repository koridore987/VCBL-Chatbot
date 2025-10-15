# DB 마이그레이션 (Alembic / Flask-Migrate)

## 개요
- Alembic은 SQLAlchemy 기반 스키마 변경을 버전으로 관리하는 도구입니다.
- 이 프로젝트는 Flask-Migrate를 통해 Alembic을 사용합니다.
- 컨테이너 시작 시 `entrypoint.sh`가 `flask db upgrade`를 자동 실행하여 최신 리비전을 적용합니다.

## 주요 개념
- upgrade: 다음 리비전으로 올리기 (테이블/컬럼/인덱스/제약 추가 등)
- downgrade: 이전 리비전으로 되돌리기 (드롭/제약 해제 등). 데이터가 삭제될 수 있으므로 주의.

## 자주 쓰는 명령
```bash
# 새로운 마이그레이션 생성 (모델 변경 후)
flask db migrate -m "explain your change"

# 최신 리비전까지 적용
flask db upgrade

# 한 단계 이전으로 되돌리기 (개발 환경에서만 권장)
flask db downgrade -1

# 현재/히스토리 확인
flask db current
flask db history
```

## 자동 실행 흐름
- Dockerfile은 컨테이너 시작 커맨드로 `backend/entrypoint.sh`를 실행합니다.
- `entrypoint.sh`는 다음을 수행합니다:
  - `python -m flask db upgrade` (모든 환경에서 자동 적용)
  - 필요 시 `python -m flask init-admin` (옵션)

## 데이터 손실 관련 주의
- upgrade라도 컬럼/테이블 삭제, 타입 축소, NOT NULL 추가(기본값 없음), 유니크 제약 추가 등은 실패/손실 유발 가능.
- downgrade는 테이블 드롭이 포함될 수 있어 데이터가 사라집니다. 운영에서는 피하고, 복구 시 스냅샷/PITR 사용을 권장.

## 참고 파일
- `backend/migrations/` (env.py, versions/*)
- `backend/entrypoint.sh`
- `backend/app/__init__.py` (Flask-Migrate 초기화)
