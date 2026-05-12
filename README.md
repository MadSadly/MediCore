# MEDI-Zero — 통합 의료 AI 진단 플랫폼

> 6종 AI 진단 모델(신부전·뇌종양·안과·척추·피부·대장암)을 통합한 의사 전용 진단 보조 시스템

---

## 목차

1. [시스템 아키텍처](#1-시스템-아키텍처)
2. [팀 구성 및 담당 모듈](#2-팀-구성-및-담당-모듈)
3. [기술 스택](#3-기술-스택)
4. [개발 시작 전 필수 설치](#4-개발-시작-전-필수-설치)
5. [로컬 개발 환경 구성](#5-로컬-개발-환경-구성)
6. [운영 배포 구조](#6-운영-배포-구조)
7. [브랜치 전략](#7-브랜치-전략)
8. [환경변수 설명](#8-환경변수-설명)
9. [API 엔드포인트](#9-api-엔드포인트)
10. [프로젝트 구조](#10-프로젝트-구조)
11. [트러블슈팅](#11-트러블슈팅)

---

## 1. 시스템 아키텍처

```
                        외부 사용자 (의사)
                               │ HTTPS
                        Cloudflare Tunnel
                               │
              ┌────────────────▼────────────────┐
              │       Master PC (192.168.0.20)  │
              │                                 │
              │  ┌──────────┐  ┌──────────────┐ │
              │  │  React   │  │ Spring Boot  │ │
              │  │  :80     │  │   :8080      │ │
              │  └────┬─────┘  └──────┬───────┘ │
              │       │  nginx ai-router :3000  │
              │       └────────┬───────┘        │
              │  ┌─────────────┤                │
              │  │ PostgreSQL  │ Redis          │
              │  │ :5432       │ :6379          │
              │  │ (pgvector)  │                │
              │  └─────────────┘                │
              └──────────────┬──────────────────┘
                             │ 유선 LAN (기가비트)
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼───────┐ ┌────────▼───────┐ ┌────────▼───────┐
│  NJ — 신부전     │ │  WJ — 뇌종양   │ │  DH — 척추     │
│  192.168.0.5    │ │  192.168.0.9   │ │  192.168.0.13  │
│  FastAPI :8000  │ │  FastAPI :8000 │ │  FastAPI :8000 │
└─────────────────┘ └────────────────┘ └────────────────┘
┌─────────▼───────┐ ┌────────▼───────┐ 
│  SH — 안과      │ │  MS — 피부      │ 
│  192.168.0.32   │ │  192.168.0.??  │ 
│  FastAPI :8000  │ │  FastAPI :8000 │
└─────────────────┘ └────────────────┘ 
```

**요청 흐름:**
```
브라우저 → nginx ai-router(:3000)
  ├── /api/**         → Spring Boot(:8080)  → PostgreSQL / Redis
  ├── /ai/kidney/**   → NJ Worker(:8000)    → 신부전 모델 + RAG
  ├── /ai/brain/**    → WJ Worker(:8000)    → 뇌종양 모델 + RAG
  ├── /ai/spine/**    → DH Worker(:8000)    → 척추 모델 + RAG
  ├── /ai/sh/**       → SH Worker(:8000)    → 안과 모델 + RAG
  └── /ai/skin/**     → MS Worker(:8000)    → 피부 모델 + RAG

```

---

## 2. 팀 구성 및 담당 모듈

| 이니셜 | 담당 질환 | AI 모델 | RAG 임베딩 | feature 브랜치 | Worker IP |
|--------|----------|---------|-----------|---------------|-----------|
| NJ | 신부전 (CKD) | TabNet 5단계 분류 | Gemini embedding | feature/kidney | 192.168.0.5 |
| WJ | 뇌종양 진단 | - | Gemini embedding | feature/brain | 192.168.0.9 |
| DH | 허리디스크 | ResNet18 | Gemini embedding | feature/spine | 192.168.0.13 |
| SH | 안과질환 | GradCAM | Gemini embedding | feature/eyes | 192.168.0.32 |
| MS | 피부질환 분류 | EfficientNet-B4 | Gemini embedding | feature/skin | 192.168.0.20 |

**작업 가능 폴더 (본인 이니셜 외 수정 금지)**
```
frontend/src/[이니셜]/
backend-main/src/.../[이니셜]/
AI/[이니셜]/
```

---

## 3. 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| **Frontend** | React + Vite + Axios | Node 20 |
| **Backend** | Spring Boot + Spring Security 7 + JPA | Java 17 |
| **AI Server** | FastAPI + PyTorch | Python 3.10 |
| **LLM** | Google Vertex AI (Gemini) | - |
| **DB** | PostgreSQL 16 + pgvector | - |
| **Cache** | Redis 7 | - |
| **Proxy** | nginx (ai-router) | alpine |
| **컨테이너** | Docker + Docker Compose | - |
| **외부 배포** | Cloudflare Tunnel | - |

---

## 4. 개발 시작 전 필수 설치

| 소프트웨어 | 확인 명령어 |
|-----------|------------|
| Docker Desktop | `docker --version` |
| JDK 17 | `java -version` |
| Node.js 20 | `node --version` |
| Python 3.10+ | `python --version` |

---

## 5. 로컬 개발 환경 구성

### Step 1 — 레포지토리 클론

```bash
git clone https://github.com/MadSadly/MediCore.git
cd MediCore
git checkout feature/[본인이니셜소문자]
```

### Step 2 — 환경변수 설정

```bash
cp .env_example .env
```

`.env`에 팀장에게 받은 값 입력:

```env
DB_PASSWORD=받은값
REDIS_PASSWORD=받은값
GCP_PROJECT_ID=받은값
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-1.5-flash-002
LANGCHAIN_API_KEY=받은값
```

### Step 3 — GCP 서비스 계정 키 배치

```bash
mkdir secrets
# 다운로드한 gcp-key.json 파일을 아래 경로에 복사
# secrets/gcp-key.json
```

### Step 4 — DB / Redis 실행 (Docker)

```bash
docker compose up postgres redis -d
```

### Step 5 — 본인 AI 서버 실행

```bash
cd AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r [이니셜]/requirements.txt
python -m [이니셜].dev_server
```

> `AI/main.py`와 `run_all.bat`은 전체 통합 실행용입니다. 로컬 개발 시에는 본인 모듈만 독립 실행하세요. `dev_server.py` 생성 방법은 `CLAUDE.md` 참고.

### Step 6 — 백엔드 실행

```bash
cd backend-main
.\gradlew.bat bootRun --args='--spring.profiles.active=local'
```

### Step 7 — 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### 정상 확인

```bash
curl http://localhost:8000/health           # AI 서버
curl http://localhost:8080/actuator/health  # Spring Boot
# 브라우저: http://localhost:5173
```

---

## 6. 운영 배포 구조

### Master PC (192.168.0.20)

```bash
# DB + 백엔드 + 프론트 + nginx ai-router 통합 실행
docker compose -f docker-compose.server.yml up -d --build
```

`docker-compose.server.yml` 구성:
- `medicore-postgres` — PostgreSQL 16 + pgvector
- `medicore-redis` — Redis 7
- `medicore-backend` — Spring Boot (prod 프로필)
- `medicore-frontend` — React (nginx 서빙)
- `medicore-ai-router` — nginx, 경로별 워커 AI 서버 라우팅, 외부 접근 포트 :3000

### Worker PC (각 담당자)

```bash
# 본인 AI 서버만 실행
docker compose -f docker-compose.ai.[이니셜소문자].yml up -d --build
```

| Compose 파일 | 담당 | 포트 |
|-------------|------|------|
| `docker-compose.ai.nj.yml` | NJ 신부전 | 8000 |
| `docker-compose.ai.wj.yml` | WJ 뇌종양 | 8000 |
| `docker-compose.ai.dh.yml` | DH 척추 | 8000 |
| `docker-compose.ai.sh.yml` | SH 안과 | 8000 |
| `docker-compose.ai.ms.yml` | MS 피부 | 8000 |

### AI 서버 환경변수 (공통)

```env
DB_URL=postgresql://medicore:${DB_PASSWORD}@192.168.0.20:5432/medicoredb
GCP_PROJECT_ID=...
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-1.5-flash-002
GCP_KEY_PATH=/app/secrets/gcp-key.json
LANGCHAIN_API_KEY=...
```

### nginx AI 라우팅 설정

`nginx/ai-proxy.conf.template` → 빌드 시 `ai-router.conf`로 적용

```nginx
location /ai/kidney/ { proxy_pass http://${WORKER_KIDNEY_IP}:8000/ai/kidney/; }
location /ai/brain/  { proxy_pass http://${WORKER_BRAIN_IP}:8000/ai/brain/;  }
location /ai/spine/  { proxy_pass http://${WORKER_SPINE_IP}:8000/ai/spine/;  }
location /ai/sh/     { proxy_pass http://${WORKER_EYES_IP}:8000/ai/sh/;      }
location /ai/skin/   { proxy_pass http://${WORKER_SKIN_IP}:8000/ai/skin/;    }
```

---

## 7. 브랜치 전략

```
main  ←── feature/kidney  (NJ)
      ←── feature/brain   (WJ)
      ←── feature/spine   (DH)
      ←── feature/eyes    (SH)
      ←── feature/skin    (MS)
```

- `main`에 직접 push 금지 — PR을 통해 머지
- 각 feature 브랜치는 main에서 분기, 완료 후 PR

### 커밋 메시지 규칙

```
feat(이니셜):     새 기능 추가
fix(이니셜):      버그 수정
refactor(이니셜): 리팩토링
docs:             문서 수정
chore:            빌드/설정 변경
```

---

## 8. 환경변수 설명

| 변수 | 설명 |
|------|------|
| `DB_PASSWORD` | PostgreSQL 비밀번호 |
| `REDIS_PASSWORD` | Redis 비밀번호 |
| `GCP_PROJECT_ID` | Google Cloud 프로젝트 ID |
| `GCP_LOCATION` | Vertex AI 리전 (기본: us-central1) |
| `GEMINI_MODEL` | 사용할 Gemini 모델명 |
| `GCP_KEY_PATH` | GCP 서비스 계정 키 경로 |
| `LANGCHAIN_API_KEY` | LangSmith 추적용 (선택) |
| `WORKER_KIDNEY_IP` ~ `WORKER_COLON_IP` | 각 워커 PC 고정 IP (nginx 라우팅용) |
| `CORS_ALLOWED_ORIGINS` | CORS 허용 오리진 |

> `.env`는 절대 git에 올리지 마세요 (`.gitignore` 등록됨).  
> `secrets/gcp-key.json`도 동일하게 git 제외됩니다.

---

## 9. API 엔드포인트

### Spring Boot (`:8080` / nginx를 통해 `:3000`)

| Method | URL | 설명 | 인증 |
|--------|-----|------|------|
| `POST` | `/api/auth/login` | 로그인 (JWT 발급) | 불필요 |
| `POST` | `/api/auth/register` | 회원가입 | 불필요 |
| `GET` | `/actuator/health` | 서버 헬스체크 | 불필요 |
| `GET` | `/api/workers` | 전체 워커 상태 + Circuit Breaker | 필요 |
| `GET` | `/api/patients` | 환자 목록 | 필요 |
| `POST` | `/api/patients` | 환자 등록 | 필요 |
| `POST` | `/api/patients/{uid}/diagnoses/kidney` | 신부전 진단 저장 | 필요 |
| `GET` | `/api/patients/{uid}/diagnoses/kidney/history` | 신부전 진단 이력 | 필요 |

### FastAPI AI 서버 (`:8000`)

| Method | URL | 설명 |
|--------|-----|------|
| `GET` | `/health` | 서버 헬스체크 |
| `GET` | `/ai/kidney/health` | 신부전 모듈 상태 |
| `POST` | `/ai/kidney/diagnose` | CKD 진단 + Alert + RAG 소견 |

### Circuit Breaker 상태 응답 예시

```json
{
  "name": "kidney",
  "status": "HEALTHY",
  "circuitState": "CLOSED",
  "failCount": 0,
  "responseTimeMs": 18,
  "lastCheckedAt": "2026-05-12T10:00:00"
}
```

---

## 10. 프로젝트 구조

```
MediCore/
├── backend-main/                  ← Spring Boot
│   └── src/main/
│       ├── java/.../
│       │   ├── auth/              ← JWT 인증 (수정 금지)
│       │   ├── SecurityConfig.java (수정 금지)
│       │   ├── worker/            ← Circuit Breaker 헬스체크
│       │   └── [이니셜]/          ← 각 담당자 API
│       └── resources/
│           ├── application.properties
│           ├── application-local.properties
│           └── db/migration/
│               ├── V1__~V4__  (공통 — 수정 금지)
│
│
├── frontend/
│   └── src/
│       ├
│       ├── WJ/ DH/ SH/ MS/ NJ/   ← 각 담당자 페이지
│       ├── App.jsx                ← 라우팅 (수정 금지)
│       └── pages/                 ← 공통 페이지 (수정 금지)
│
├── AI/
│   │ 
│   ├── WJ/ DH/ SH/ MS/ NJ/        ← 각 담당자 AI 모듈
│   ├── main.py                    ← 통합 진입점 (수정 금지)
│   └── requirements.txt           ← 공통 패키지 (수정 금지)
│
├── nginx/
│   ├── ai-proxy.conf.template     ← 워커 라우팅 템플릿
│   └── ai-router.conf             ← 실제 적용 설정
│
├── postgres/
│   └── initdb.d/01_init.sql       ← pgvector 초기화
│
├── docker-compose.yml             ← 로컬 개발용 (DB + 전체 스택)
├── docker-compose.server.yml      ← Master PC 운영용
├── docker-compose.ai.[이니셜].yml ← 각 워커 운영용
├── run_all.bat                    ← 로컬 개발 통합 실행 (수정 금지)
├── .env_example                   ← 환경변수 템플릿
├── CLAUDE.md                      ← AI 작업 규칙
└── README.md
```

---

## 11. 트러블슈팅

### Spring Boot가 DB 연결 실패로 종료됨

```bash
docker compose up postgres redis -d  # DB를 먼저 띄운 후 백엔드 실행
docker ps                            # medicore-postgres 상태 확인
```

### FastAPI 실행 시 ModuleNotFoundError

```bash
cd AI
venv\Scripts\activate
pip install -r requirements.txt
pip install -r [이니셜]/requirements.txt
```

### AI 서버는 떠있는데 진단 요청이 실패함

- JWT 토큰 만료 여부 확인 (30분 TTL) — 재로그인 후 재시도
- `GET /ai/kidney/health`로 모델 로드 상태 확인
- Circuit Breaker가 OPEN 상태인 경우 `GET /api/workers`로 확인

### Korean 텍스트가 포함된 JSON을 curl로 보낼 때 400 오류

```bash
# 인라인 -d '{"query":"한글..."}' 대신 파일 사용
echo '{"query":"한글 질의"}' > req.json
curl -X POST ... -d @req.json
```

### 특정 워커가 Circuit Breaker OPEN 상태

→ 해당 워커 PC에서 AI 서버가 내려간 상태  
→ `docker compose -f docker-compose.ai.[이니셜].yml restart`로 재시작  
→ 복구 후 30초 이내 자동으로 CLOSED 상태 전환

### gradlew 실행 오류 (Windows)

```bash
# gradlew 단독 실행 금지 — 반드시 아래 명령어 사용
.\gradlew.bat bootRun
```
