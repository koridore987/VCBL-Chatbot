# VCBL 챗봇 프로젝트

Flask 기반의 챗봇 웹 애플리케이션입니다.

## 📁 프로젝트 구조

```
vcbl-chatbot/
├── app/                          # 메인 애플리케이션 패키지
│   ├── __init__.py              # Flask 앱 팩토리
│   ├── config.py                # 애플리케이션 설정
│   ├── models/                  # 데이터 모델
│   │   ├── __init__.py          # DatabaseManager
│   │   └── admin.py             # AdminManager
│   ├── routes/                  # 라우트 (블루프린트)
│   │   ├── __init__.py
│   │   ├── auth.py              # 인증 라우트
│   │   ├── chat.py              # 채팅 라우트
│   │   └── admin.py             # 관리자 라우트
│   ├── services/                # 비즈니스 로직
│   │   └── __init__.py          # ChatService
│   ├── utils/                   # 유틸리티 함수
│   │   └── __init__.py          # 데이터베이스 초기화
│   ├── static/                  # 정적 파일 (CSS, JS, 이미지)
│   │   └── style.css
│   └── templates/               # HTML 템플릿
│       ├── admin/               # 관리자 템플릿
│       │   ├── admin_management.html
│       │   ├── dashboard.html
│       │   ├── login.html
│       │   ├── user_detail.html
│       │   └── user_management.html
│       ├── about.html
│       ├── error.html
│       ├── index.html
│       ├── login.html
│       └── register.html
├── run.py                       # 서버 실행 파일
├── requirements.txt             # Python 의존성
├── chatbot.db                   # SQLite 데이터베이스
└── README.md                    # 프로젝트 문서
```

## 🚀 실행 방법

1. **가상환경 활성화**:
   ```bash
   source .venv/bin/activate
   ```

2. **서버 실행**:
   ```bash
   python run.py
   ```

3. **접속**:
   - 메인 페이지: http://localhost:8080/
   - 관리자 로그인: http://localhost:8080/admin/login

## 🔧 주요 기능

### 사용자 기능
- 회원가입/로그인
- 실시간 채팅 (OpenAI GPT-4o-mini)
- 채팅 기록 저장

### 관리자 기능
- 회원 관리 (목록, 상세보기, 삭제)
- 회원 일괄 등록 (엑셀 업로드)
- 프롬프트 관리 (챗봇 타입 생성/수정/삭제)
- 채팅 로그 내보내기 (CSV/Excel)
  - 전체 로그 내보내기
  - 사용자별 로그 내보내기
  - 날짜 범위별 로그 내보내기
- 회원 통계 대시보드
- 관리자 계정 관리
- 채팅 기록 조회

## 📊 기본 관리자 계정

- **ID**: `super`
- **비밀번호**: `super123`

## 🛠️ 기술 스택

- **Backend**: Flask, SQLite3
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI**: OpenAI GPT-4o-mini
- **Authentication**: Cookie-based
- **Database**: SQLite3

## 📝 개발 가이드

### 새로운 라우트 추가
1. `app/routes/` 디렉토리에 새 파일 생성
2. Blueprint 생성 및 라우트 정의
3. `app/__init__.py`에서 Blueprint 등록

### 새로운 모델 추가
1. `app/models/` 디렉토리에 새 파일 생성
2. 데이터베이스 관련 클래스 정의
3. 필요한 곳에서 import하여 사용

### 새로운 서비스 추가
1. `app/services/` 디렉토리에 새 파일 생성
2. 비즈니스 로직 클래스 정의
3. 라우트에서 서비스 사용

## 🔒 보안

- 비밀번호 SHA-256 해시화
- 쿠키 기반 인증
- 관리자 권한 분리 (super, admin)
- 입력 검증 및 에러 처리
