@echo off
REM 멀티 플랫폼 Docker 빌드 스크립트 (Windows용)

echo 🚀 멀티 플랫폼 Docker 빌드 시작...

REM Docker Buildx 활성화
echo 🔧 Docker Buildx 설정...
docker buildx create --use --name multiarch-builder 2>nul
docker buildx use multiarch-builder

REM Windows에서는 AMD64 플랫폼 사용
echo 🏗️ Windows용 빌드 (AMD64)...
docker buildx build --platform linux/amd64 -t vcbl-chatbot:latest .

if %ERRORLEVEL% EQU 0 (
    echo ✅ 빌드 완료!
    echo 🚀 Docker Compose로 실행하려면: docker-compose up
) else (
    echo ❌ 빌드 실패!
    exit /b 1
)
