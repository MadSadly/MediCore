@echo off
chcp 65001 > nul
echo.
echo ====================================
echo   MEDI-Zero 로컬 개발 환경 시작
echo ====================================
echo.

:: 프로젝트 루트 경로 (이 파일 위치 기준)
set ROOT=%~dp0

:: ── 1. PostgreSQL + Redis 시작 ──────────────────────────────────
echo [1/4] PostgreSQL + Redis 시작 중...
docker compose -f "%ROOT%docker-compose.yml" up postgres redis -d
if %errorlevel% neq 0 (
    echo [ERROR] Docker 실행 실패. Docker Desktop이 켜져있는지 확인하세요.
    pause
    exit /b 1
)

:: ── 2. DB 헬스체크 대기 ──────────────────────────────────────────
echo.
echo [2/4] DB 헬스체크 대기 중 (최대 30초)...
set /a count=0
:wait_loop
    docker inspect --format="{{.State.Health.Status}}" medizero-postgres 2>nul | findstr "healthy" > nul
    if %errorlevel% equ 0 goto db_ready
    set /a count+=1
    if %count% geq 15 (
        echo [ERROR] PostgreSQL 헬스체크 타임아웃. 컨테이너 상태를 확인하세요.
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak > nul
    goto wait_loop

:db_ready
echo [OK] PostgreSQL + Redis 준비 완료!
echo.

:: ── 3. Spring Boot 백엔드 ────────────────────────────────────────
echo [3/4] Spring Boot 백엔드 시작 중...
start "MEDI-Zero Backend :8080" cmd /k "chcp 65001 > nul && cd /d %ROOT%backend-main && gradlew.bat bootRun --args=--spring.profiles.active=local"

:: ── 4. FastAPI AI 서버 ───────────────────────────────────────────
echo [4/4] FastAPI AI 서버 시작 중...
start "MEDI-Zero AI Server :8000" cmd /k "chcp 65001 > nul && cd /d %ROOT%AI && (if not exist venv python -m venv venv) && call venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: ── 5. React 프론트엔드 ──────────────────────────────────────────
echo [5/4] React 프론트엔드 시작 중...
start "MEDI-Zero Frontend :5173" cmd /k "chcp 65001 > nul && cd /d %ROOT%frontend && (if not exist node_modules npm install) && npm run dev"

echo.
echo ====================================
echo   모든 서비스 시작 완료!
echo ====================================
echo.
echo   Frontend  : http://localhost:5173
echo   Backend   : http://localhost:8080
echo   AI Server : http://localhost:8000
echo   PostgreSQL: localhost:5432
echo   Redis     : localhost:6379
echo.
echo   종료하려면 각 터미널을 닫고 아래 명령어 실행:
echo   docker compose stop
echo.
pause