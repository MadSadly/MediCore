# 개발 환경 세팅 가이드 (CMD 기준)

---

## 0. 공통 설치 (제일 먼저)

**Docker Desktop**
- https://www.docker.com/products/docker-desktop 에서 다운로드
- 설치 후 PC 재시작
- 재시작 후 Docker Desktop 실행 (트레이 아이콘에 고래 뜨면 준비 완료)

설치 확인:
```cmd
docker --version
docker compose version
```

---

## 1. 프로젝트 클론

```cmd
cd C:\Users\본인이름\Desktop
git clone https://github.com/팀레포주소.git
cd MediCore

자세한 내용은 githubGuide.md 에서 확인
```

---
이미 깔려있을수 있으니 cmd에서 먼저 체크부터하고 진행합시다..

## 2. 프론트엔드 (React)

**설치할 것:** Node.js 20
- https://nodejs.org 에서 LTS 버전 다운로드 후 설치

설치 확인 및 패키지 설치:
```cmd
node --version
npm --version

cd C:\Users\본인이름\Desktop\MediCore\frontend
npm install
```

`node_modules` 폴더가 생기면 완료.

---

## 3. 백엔드 (Spring Boot)

**설치할 것:** JDK 17
- https://adoptium.net 에서 Temurin 17 다운로드 후 설치
- 설치 중 **"Add to PATH"** 체크 필수

설치 확인 및 빌드:
```cmd
java --version

cd C:\Users\본인이름\Desktop\MediCore\backend-main
gradlew.bat build -x test
```

`BUILD SUCCESSFUL` 나오면 완료.

---

## 4. AI 서버 (FastAPI)

**설치할 것:** Python 3.10
- https://www.python.org/downloads 에서 3.10 다운로드
- 설치 중 **"Add Python to PATH"** 체크 필수

설치 확인 및 가상환경 생성 후 패키지 설치:
```cmd
python --version

cd C:\Users\본인이름\Desktop\MediCore\AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`(venv)` 가 앞에 붙으면 가상환경 진입 완료. 이후 작업은 항상 venv 안에서 진행.

---

## 5. 환경변수 설정 (.env)

Docker 실행 전 필수. 루트 폴더에 `.env` 파일을 만들어야 함.

```cmd
cd C:\Users\본인이름\Desktop\MediCore
copy .env_example .env
```

`.env` 파일을 메모장으로 열어서 비밀번호 직접 설정:

```
DB_PASSWORD=원하는비밀번호
REDIS_PASSWORD=원하는비밀번호
```

> `.env` 파일은 git에 올라가지 않음. 본인 PC에만 존재.

---

## 6. DB (PostgreSQL)

별도 설치 없음. Docker가 자동으로 실행해줌.

---

## 7. 실행 방법

### 한 번에 전부 실행 (개발할 때)

세팅이 전부 완료됐으면 프로젝트 루트의 `run_all.bat` 을 실행
cmd 창에서 run_all.bat 실행
예) 

- PostgreSQL + Redis → Docker로 자동 실행
- Spring Boot, FastAPI, React → 각각 새 터미널 창에서 자동 실행

| 서비스 | 주소 |
|--------|------|
| 프론트엔드 | http://localhost:5173 |
| 백엔드 | http://localhost:8080 |
| AI 서버 | http://localhost:8000 |

종료할 때:
```cmd
docker compose stop
```
각 터미널 창도 닫으면 됨.

---

### 수동으로 실행할 때 (마지막에 배포전까지는 ### 개발할때 를 참조하세요)

### 한 번에 전부 실행 (처음 세팅 확인할 때)

프로젝트 루트에서:
```cmd
cd C:\Users\본인이름\Desktop\MediCore
docker compose up -d
```

브라우저에서 `http://localhost:3000` 접속되면 세팅 완료.

종료:
```cmd
docker compose down
```

---

### 개발할 때 (코드 수정하면서 작업할 때)

CMD 창 4개 띄워서 각각 실행.

**창 1 - DB만 Docker로**
```cmd
cd C:\Users\본인이름\Desktop\MediCore
docker compose up db -d
```

**창 2 - Spring Boot**
```cmd
cd C:\Users\본인이름\Desktop\MediCore\backend-main
gradlew.bat bootRun
```

**창 3 - React**
```cmd
cd C:\Users\본인이름\Desktop\MediCore\frontend
npm run dev
```

**창 4 - AI 서버**
```cmd
cd C:\Users\본인이름\Desktop\MediCore\AI
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

브라우저: `http://localhost:5173`

> 코드 수정하면 저장만 해도 자동으로 반영됨. docker compose 다시 안 해도 됨.

---

## 요약

| 서버 | 설치 | 명령어 치는 위치 |
|------|------|----------------|
| 프론트 | Node.js 20 | `MediCore/frontend/` |
| 백엔드 | JDK 17 | `MediCore/backend-main/` |
| AI | Python 3.10 | `MediCore/AI/` |
| DB | 없음 (Docker) | - |
| 전체 실행 | Docker Desktop | `MediCore/` (루트) |

설치 순서: **Docker Desktop → Node.js → JDK → Python**
전부 설치 중 PATH 옵션 체크 필수.
