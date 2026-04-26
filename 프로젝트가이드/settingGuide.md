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
```

---

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

**설치할 것:** Python 3.11
- https://www.python.org/downloads 에서 3.11 다운로드
- 설치 중 **"Add Python to PATH"** 체크 필수

설치 확인 및 패키지 설치:
```cmd
python --version

cd C:\Users\본인이름\Desktop\MediCore\AI
pip install -r requirements.txt
```

---

## 5. DB (PostgreSQL)

별도 설치 없음. Docker가 자동으로 실행해줌.

---

## 6. 실행 방법

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
| AI | Python 3.11 | `MediCore/AI/` |
| DB | 없음 (Docker) | - |
| 전체 실행 | Docker Desktop | `MediCore/` (루트) |

설치 순서: **Docker Desktop → Node.js → JDK → Python**
전부 설치 중 PATH 옵션 체크 필수.
