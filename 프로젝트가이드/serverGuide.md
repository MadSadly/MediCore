# MediCore 서버 구성 및 배포 전략

---

## 프로젝트에서 사용하는 서버

총 10개의 서버(컨테이너)로 구성됨.

| 서버 | 역할 |
|------|------|
| **React (Frontend)** | 사용자가 접속하는 화면. 진단 요청 및 결과 출력 |
| **Spring Boot (Backend)** | API 서버. 요청을 받아 각 AI 서버로 라우팅 |
| **PostgreSQL + pgvector** | 데이터 저장. 진단 결과 및 RAG 벡터 데이터 보관 |
| **Redis** | 세션 및 캐시. 빠른 임시 데이터 처리 |
| **FastAPI AI x6** | 각 담당 진단 모듈. 학습 모델 실행 후 LLM+RAG로 결과 생성 |

---

## AI 서버 담당 모듈

| PC IP | 담당 |
|-------|------|
| 192.168.0.20 | 피부 진단 |
| 192.168.0.9  | 뇌종양 진단 |
| 192.168.0.32 | 안과 진단 |
| 192.168.0.13 | 척추 진단 |
| 192.168.0.5  | 신장 진단 |
| 192.168.0.73 | 대장암 진단 |

---

## 전체 요청 흐름

```
사용자
  ↓
React (화면)
  ↓
Spring Boot (요청 분배)
  ├── PostgreSQL (데이터 저장/조회)
  ├── Redis (캐시)
  └── FastAPI AI 서버 (진단 요청)
          ↓
      학습 모델 추론
          ↓
      LLM + RAG 결과 생성
          ↓
Spring Boot → React → 사용자
```

이 서버들이 전부 정상 실행되면 프로젝트가 동작함.

---

## 배포 전략

### 원래 계획 (Docker Compose 단일 서버)

원래는 서버 한 대에 `docker compose up` 한 번으로 전체를 올리는 구조였음.

```
[서버 1대]
  ├── React
  ├── Spring Boot
  ├── PostgreSQL
  ├── Redis
  └── FastAPI AI x6 (모델 6개 전부)
```

**문제:** AI 모델 6개를 한 PC에서 동시에 올리면 RAM 부족으로 실행 불가. 학원 PC 사양으로는 감당이 안 됨.

---

### 현재 계획 (각자 PC를 서버로 사용)

각자 PC에 본인 담당 AI 서버만 올리고, Master PC 한 대에 공통 서버를 올리는 분산 구조.

```
Master PC (192.168.0.39)
  ├── React
  ├── Spring Boot   ─── 각 Worker PC의 AI 서버를 IP로 직접 호출
  ├── PostgreSQL
  └── Redis

Worker PC x6 (각자 PC)
  └── FastAPI AI 서버 (본인 담당 모듈만 실행)
```

Spring Boot가 요청을 받으면 해당 AI 서버의 IP로 직접 HTTP 요청을 보내는 방식.

---

## 로컬 개발 방법

DB + Redis만 Docker로 올리고 나머지는 직접 실행. 저장하면 바로 반영됨.
`run_[이니셜].bat` 더블클릭하면 아래 과정이 자동으로 실행됨. (만드는 방법은 `CLAUDE.md` 참고)

**창 1 - DB + Redis**
```cmd
docker compose up postgres redis -d
```

**창 2 - Spring Boot**
```cmd
cd backend-main
gradlew.bat bootRun
```

**창 3 - React**
```cmd
cd frontend
npm run dev
```

**창 4 - AI 서버 (본인 모듈만 독립 실행)**
```cmd
cd AI
python -m [이니셜].dev_server
```

> ⚠ `uvicorn main:app`으로 실행하면 한 명 코드 오류 시 전체가 서버가 안 뜹니다.
> 반드시 본인 `AI/[이니셜]/dev_server.py`로 실행하세요.

---

## 시연 배포 방법 (최종)

시연 당일 PC 7대를 아래와 같이 구성합니다.

### Master PC 1대 (React + Spring + DB + Redis)

```cmd
cd MediCore
docker compose up postgres redis -d
cd backend-main && gradlew.bat bootRun
cd frontend && npm run dev
```

### Worker PC 6대 (각자 AI 서버)

각자 본인 폴더의 `Dockerfile`로 빌드 후 실행합니다.

```cmd
cd D:\workspace\MediCore\AI

:: 빌드
docker build -f [이니셜]/Dockerfile -t medicore-[이니셜] .

:: 실행
docker run -p 8000:8000 --env-file ../.env medicore-[이니셜]
```

예) WJ:
```cmd
docker build -f WJ/Dockerfile -t medicore-wj .
docker run -p 8000:8000 --env-file ../.env medicore-wj
```

> 각자 `AI/[이니셜]/Dockerfile`이 있어야 합니다. 없으면 `CLAUDE.md` 참고해서 만드세요.

---

## 코드 관리 (Git)

각자 본인 브랜치에서 작업 후 main으로 PR.

```
feature/본인모듈  →  main
```

자세한 내용은 `githubGuide.md` 참고.
