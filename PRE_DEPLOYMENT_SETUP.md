# 🚀 VCBL Chatbot - 사전 배포 설정 가이드

이 문서는 VCBL Chatbot을 Google Cloud에 배포하기 전에 Google Cloud Console에서 미리 설정해야 하는 작업들을 안내합니다.

## 📋 사전 설정 체크리스트

### 1. Google Cloud 프로젝트 생성 및 설정

#### 1.1 새 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단의 프로젝트 선택 드롭다운 클릭
3. "새 프로젝트" 클릭
4. 프로젝트 이름 입력 (예: `vcbl-chatbot-prod`)
5. 조직 선택 (있는 경우)
6. "만들기" 클릭

#### 1.2 결제 계정 연결
1. [결제](https://console.cloud.google.com/billing) 페이지로 이동
2. "결제 계정 연결" 클릭
3. 새 결제 계정 생성 또는 기존 계정 선택
4. 프로젝트에 결제 계정 연결

### 2. Cloud SQL 인스턴스 생성

#### 2.1 PostgreSQL 인스턴스 생성
1. [Cloud SQL](https://console.cloud.google.com/sql) 페이지로 이동
2. "인스턴스 만들기" 클릭
3. "PostgreSQL" 선택
4. 인스턴스 설정:
   - **인스턴스 ID**: `vcbl-chatbot-db`
   - **비밀번호**: 강력한 비밀번호 설정 (나중에 필요)
   - **데이터베이스 버전**: PostgreSQL 15
   - **리전**: `asia-northeast3` (서울)
   - **영역**: `asia-northeast3-a`
   - **머신 유형**: `db-f1-micro` (개발용) 또는 `db-g1-small` (프로덕션용)
   - **스토리지**: SSD, 10GB 이상
5. "만들기" 클릭

#### 2.2 데이터베이스 생성
1. 생성된 인스턴스 클릭
2. "데이터베이스" 탭으로 이동
3. "데이터베이스 만들기" 클릭
4. 데이터베이스 이름: `vcbl_chatbot`
5. "만들기" 클릭

#### 2.3 사용자 생성
1. "사용자" 탭으로 이동
2. "사용자 계정 추가" 클릭
3. 사용자 이름: `vcbl_user`
4. 비밀번호: 강력한 비밀번호 설정
5. "추가" 클릭

### 3. IAM 권한 설정

#### 3.1 서비스 계정 확인 또는 생성
1. [IAM 및 관리자 > 서비스 계정](https://console.cloud.google.com/iam-admin/serviceaccounts) 페이지로 이동
2. `vcbl-deployer` 서비스 계정이 있는지 확인
3. **기존 계정이 있는 경우**: 3.2로 이동
4. **기존 계정이 없는 경우**: 새로 생성
   - "서비스 계정 만들기" 클릭
   - 서비스 계정 세부정보:
     - **이름**: `vcbl-deployer`
     - **ID**: `vcbl-deployer`
     - **설명**: `VCBL Chatbot Deployer Service Account`
   - "만들기 및 계속하기" 클릭

#### 3.2 서비스 계정 권한 부여
다음 역할들을 부여:
- **Cloud Run 개발자** (`roles/run.developer`)
- **Cloud SQL 클라이언트** (`roles/cloudsql.client`)
- **Secret Manager 시크릿 액세스** (`roles/secretmanager.secretAccessor`)
- **Cloud Build 편집자** (`roles/cloudbuild.builds.editor`)
- **Storage 관리자** (`roles/storage.admin`)

#### 3.3 서비스 계정 키 생성 (선택사항)
1. 생성된 서비스 계정 클릭
2. "키" 탭으로 이동
3. "키 추가" > "새 키 만들기" 클릭
4. "JSON" 선택
5. 키 파일 다운로드 (로컬 개발용)

### 4. Artifact Registry 설정

#### 4.1 Artifact Registry 저장소 생성
1. [Artifact Registry](https://console.cloud.google.com/artifacts) 페이지로 이동
2. "저장소 만들기" 클릭
3. 저장소 설정:
   - **저장소 이름**: `vcbl-chatbot-repo`
   - **형식**: Docker
   - **모드**: 표준
   - **리전**: `asia-northeast3`
4. "만들기" 클릭

### 5. Cloud Build 설정

#### 5.1 Cloud Build API 활성화
1. [Cloud Build](https://console.cloud.google.com/cloud-build) 페이지로 이동
2. API가 자동으로 활성화됨

#### 5.2 GitHub 연결 (선택사항)
1. "트리거" 탭으로 이동
2. "트리거 만들기" 클릭
3. 소스: GitHub 선택
4. GitHub 저장소 연결
5. 설정은 나중에 스크립트에서 자동으로 처리됨

### 6. Secret Manager 설정

#### 6.1 Secret Manager API 활성화
1. [Secret Manager](https://console.cloud.google.com/security/secret-manager) 페이지로 이동
2. API가 자동으로 활성화됨

### 7. 네트워킹 설정 (선택사항)

#### 7.1 VPC 네트워크 설정 (고급)
- 기본 VPC 네트워크 사용 권장
- 필요시 커스텀 VPC 생성

#### 7.2 방화벽 규칙 (필요시)
- 기본 설정으로 충분
- 특별한 보안 요구사항이 있는 경우 추가 설정

## 🔧 gcloud CLI 설정

### 1. gcloud CLI 설치
```bash
# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 또는 Homebrew 사용
brew install google-cloud-sdk
```

### 2. gcloud 초기화
```bash
gcloud init
```

### 3. 프로젝트 설정
```bash
gcloud config set project YOUR_PROJECT_ID
```

### 4. 인증 확인
```bash
gcloud auth list
gcloud config list
```

## 📝 배포 전 확인사항

### 필수 정보 수집
배포 스크립트 실행 전에 다음 정보들을 준비하세요:

1. **프로젝트 ID**: Google Cloud Console에서 확인
2. **Cloud SQL 인스턴스 연결 문자열**: 
   - 형식: `PROJECT_ID:REGION:INSTANCE_NAME`
   - 예: `my-project:asia-northeast3:vcbl-chatbot-db`
3. **데이터베이스 비밀번호**: Cloud SQL에서 설정한 비밀번호
4. **GitHub 저장소 정보**: 소유자명, 저장소명
5. **시크릿 값들**:
   - SECRET_KEY (Flask 시크릿 키)
   - JWT_SECRET_KEY (JWT 토큰 시크릿)
   - OPENAI_API_KEY (OpenAI API 키)

### 기존 서비스 계정 활용
`vcbl-deployer` 서비스 계정이 이미 있는 경우:
- 스크립트가 자동으로 기존 계정을 감지하고 권한을 업데이트합니다
- 추가 서비스 계정 생성이 필요하지 않습니다
- 필요한 IAM 역할들이 자동으로 부여됩니다

### 비용 예상
- **Cloud SQL**: 월 $7-15 (db-f1-micro 기준)
- **Cloud Run**: 사용량 기반 (무료 할당량 있음)
- **Artifact Registry**: 저장소 크기 기반 (무료 할당량 있음)
- **Secret Manager**: 시크릿 개수 기반 (무료 할당량 있음)

## 🚀 다음 단계

모든 사전 설정이 완료되면:

1. `my_deploy_script.sh` 스크립트 실행
2. 스크립트에서 요구하는 정보 입력
3. 배포 완료 후 서비스 테스트

## 🔍 문제 해결

### 일반적인 문제들
1. **API 활성화 오류**: 프로젝트에 결제 계정이 연결되어 있는지 확인
2. **권한 오류**: IAM 설정에서 필요한 역할이 부여되었는지 확인
3. **Cloud SQL 연결 오류**: 인스턴스가 실행 중인지 확인
4. **빌드 오류**: Docker 이미지가 올바르게 빌드되는지 확인

### 유용한 명령어들
```bash
# 프로젝트 설정 확인
gcloud config list

# API 활성화 상태 확인
gcloud services list --enabled

# Cloud SQL 인스턴스 목록
gcloud sql instances list

# 서비스 계정 권한 확인
gcloud projects get-iam-policy PROJECT_ID
```

이제 모든 사전 설정이 완료되었습니다! 🎉
