# MEDI-Zero — 통합 의료 AI 진단 플랫폼

> 7종의 AI 진단 모델(피부·뇌종양·안과·척추·신장·대장암)을 통합한 의사 전용 진단 보조 시스템

---

## 목차

1. [시스템 아키텍처](#1-시스템-아키텍처)
2. [기술 스택](#2-기술-스택)
3. [개발 시작 전 필수 설치](#3-개발-시작-전-필수-설치)
4. [처음 시작하는 팀원 (온보딩)](#4-처음-시작하는-팀원-온보딩)
5. [로컬 개발 방법](#5-로컬-개발-방법)
6. [브랜치 전략](#6-브랜치-전략)
7. [CI 자동 테스트](#7-ci-자동-테스트)
8. [환경변수 설명](#8-환경변수-설명)
9. [배포 구조 (운영)](#9-배포-구조-운영)
10. [워커 PC 세팅 방법](#10-워커-pc-세팅-방법)
11. [API 엔드포인트](#11-api-엔드포인트)
12. [자주 묻는 질문 / 트러블슈팅](#12-자주-묻는-질문--트러블슈팅)

---

## 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        외부 사용자 (의사)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                     Cloudflare Tunnel
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     Master PC (192.168.0.39)                     │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────┐ │
│  │    React    │  │ Spring Boot  │  │ PostgreSQL  │  │ Redis  │ │
│  │  :3000      │◄─┤    :8080     ├──┤ :5432       │  │ :6379  │ │
│  │  (Nginx)    │  │              │  │ (pgvector)  │  │        │ │
│  └─────────────┘  └──────┬───────┘  └────────────┘  └────────┘ │
│                          │ 5초마다 헬스체크 (Circuit Breaker)    │
└──────────────────────────┼──────────────────────────────────────┘
                           │ 유선 LAN (기가비트)
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
│  Worker 1      │ │  Worker 2    │ │  Worker 3    │
│  피부 진단     │ │  뇌종양 진단  │ │  안과 진단   │
│  :192.168.0.20 │ │:192.168.0.9  │ │:192.168.0.32 │
│  FastAPI :8000 │ │FastAPI :8000 │ │FastAPI :8000 │
│  gemini-embedding-001+Gemini │ │gemini-embedding-001+Gemini │ │gemini-embedding-001+Gemini │
└────────────────┘ └──────────────┘ └──────────────┘
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
│  Worker 4      │ │  Worker 5    │ │  Worker 6    │
│  척추 진단     │ │  신장 진단   │ │  대장암 진단  │
│  :192.168.0.13 │ │:192.168.0.5  │ │:192.168.0.73 │
│  FastAPI :8000 │ │FastAPI :8000 │ │FastAPI :8000 │
│  gemini-embedding-001+Gemini │ │gemini-embedding-001+Gemini │ │gemini-embedding-001+Gemini │
└────────────────┘ └──────────────┘ └──────────────┘
```

**데이터 흐름:**
```
사용자 요청 → React → Spring Boot → 해당 Worker FastAPI
                                  ↓
                         AI 모델 추론 (PyTorch / YOLO)
                                  ↓
                      RAG 검색 (gemini-embedding-001 768차원 → pgvector)
                                  ↓
                      LLM 소견서 생성 (Ollama GGUF)
                                  ↓
                      Spring Boot → React → 사용자
```

---

## 2. 기술 스택

| 영역 | 기술 | 버전 |
|---|---|---|
| **Frontend** | React + TailwindCSS + Axios | Node 20 |
| **Backend** | Spring Boot + JPA + Spring Security | Java 17 |
| **AI Server** | FastAPI + PyTorch + YOLOv8 | Python 3.10+ |
| **LLM** | Google Vertex AI Gemini 1.5 Flash/Pro | - |
| **RAG 임베딩** | Google gemini-embedding-001 (768차원) | - |
| **DB** | PostgreSQL 16 + pgvector | - |
| **Cache** | Redis 7 | - |
| **DevOps** | Docker, GitHub Actions | - |
| **외부 배포** | Cloudflare Tunnel | - |

---

## 3. 개발 시작 전 필수 설치

> 아래 4가지가 없으면 `run_all.bat`이 실행되지 않습니다.

| 소프트웨어 | 다운로드 | 확인 명령어 |
|---|---|---|
| **Docker Desktop** | https://www.docker.com/products/docker-desktop | `docker --version` |
| **JDK 17** | https://adoptium.net | `java -version` |
| **Node.js 20** | https://nodejs.org | `node --version` |
| **Python 3.10+** | https://python.org | `python --version` |

---

## 4. 처음 시작하는 팀원 (온보딩)

> **팀장에게 `.env` 파일 비밀번호를 슬랙 DM으로 받은 후 진행하세요.**

### Step 1 — 레포지토리 클론

```bash
git clone https://github.com/MadSadly/MediCore.git
cd MediCore
```

### Step 2 — 환경변수 파일 생성

```bash
# 템플릿 복사
cp .env_example .env
```

`.env` 파일을 열어서 팀장에게 받은 비밀번호로 채우세요:

```env
DB_PASSWORD=팀장에게받은값
REDIS_PASSWORD=팀장에게받은값
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Step 3 — FastAPI 패키지 설치 (최초 1회)

```bash
cd AI
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cd ..
```

> ⚠️ AI 패키지가 많아서 5~10분 소요됩니다. 커피 한 잔 하세요.

### Step 4 — 개발 서버 실행

```bash
# 이걸 더블클릭하면 끝!
run_all.bat
```

터미널 3개가 자동으로 열립니다:

| 터미널 | 서비스 | 주소 |
|---|---|---|
| MEDI-Zero Backend :8080 | Spring Boot | http://localhost:8080 |
| MEDI-Zero AI Server :8000 | FastAPI | http://localhost:8000 |
| MEDI-Zero Frontend :5173 | React (Vite) | http://localhost:5173 |

### Step 5 — 정상 실행 확인

```bash
# Spring Boot 헬스체크
curl http://localhost:8080/actuator/health

# FastAPI 헬스체크
curl http://localhost:8000/health

# 브라우저에서 React 확인
# → http://localhost:5173 접속
```

---

## 5. 로컬 개발 방법

### 기본 구조

```
로컬 개발 환경
├── Docker (자동 실행)
│   ├── PostgreSQL :5432  ← DB
│   └── Redis :6379       ← 캐시
│
├── 터미널 1: Spring Boot (application-local.properties 적용)
├── 터미널 2: FastAPI (venv 활성화 후 uvicorn)
└── 터미널 3: React (Vite dev server)
```

### 수동으로 각 서비스 실행하는 방법

**DB만 Docker로 띄우기:**
```bash
docker compose up postgres redis -d
```

**Spring Boot:**
```bash
cd backend-main
./gradlew bootRun --args='--spring.profiles.active=local'
```

**FastAPI (본인 모듈만 독립 실행):**
```bash
cd AI
venv\Scripts\activate
python -m [이니셜].dev_server
```
> ⚠ `uvicorn main:app` 대신 본인 `dev_server.py`로 실행. 만드는 방법은 `CLAUDE.md` 참고.

**React:**
```bash
cd frontend
npm run dev
```

### Spring Boot 프로필 설명

| 프로필 | 언제 | DB |
|---|---|---|
| `local` | 로컬 개발 | Docker PostgreSQL (localhost:5432) |
| `test` | CI / 단위 테스트 | H2 인메모리 (외부 의존성 없음) |
| `prod` | 운영 배포 | 환경변수로 주입 |

### 개발 종료

```bash
# Docker 컨테이너 중지 (데이터 보존)
docker compose stop

# 완전 삭제 (데이터도 삭제됨 - 주의!)
docker compose down -v
```

---

## 6. 브랜치 전략

```
main         ← 배포 브랜치 (직접 push 금지, PR만 허용)
  └── develop    ← 개발 통합 브랜치
        ├── feature/skin        ← 피부 진단 기능
        ├── feature/brain       ← 뇌종양 진단 기능
        ├── feature/eyes        ← 안과 진단 기능
        ├── feature/spine       ← 척추 진단 기능
        ├── feature/kidney      ← 신장 진단 기능
        ├── feature/colon       ← 대장암 진단 기능
        ├── feature/login       ← 로그인/인증
        └── feature/main-page   ← 메인 페이지
```

### 작업 흐름

```bash
# 1. develop 최신 상태로 동기화
git checkout develop
git pull origin develop

# 2. 내 feature 브랜치 생성
git checkout -b feature/내기능명

# 3. 작업 후 커밋
git add .
git commit -m "feat: 피부 진단 결과 화면 추가"

# 4. develop에 PR 올리기
git push origin feature/내기능명
# → GitHub에서 Pull Request 생성 → 팀원 리뷰 → Merge
```

### 커밋 메시지 규칙

```
feat:     새 기능 추가
fix:      버그 수정
refactor: 코드 리팩토링
docs:     문서 수정
test:     테스트 추가
chore:    빌드/설정 변경
```

---

## 7. CI 자동 테스트

`main` 또는 `develop` 브랜치에 push / PR 생성 시 **자동으로** 실행됩니다.

```
GitHub Actions CI 파이프라인

push / PR
    │
    ├── backend-unit       H2 인메모리로 단위 테스트 (빠름, ~1분)
    ├── backend-integration  실제 PostgreSQL+Redis로 통합 테스트 (~3분)
    ├── frontend           npm lint + build 검증 (~2분)
    │
    └── docker-build       (main push 시만) Docker 이미지 빌드 검증
```

> CI가 **빨간불**이면 Merge 하지 마세요. 본인 브랜치에서 먼저 고쳐야 합니다.

---

## 8. 환경변수 설명

`.env_example`을 복사해서 `.env`로 만든 후 값을 채웁니다.  
`.env`는 **절대 git에 올리지 마세요** (`.gitignore`에 등록되어 있음).

| 변수 | 설명 | 예시 |
|---|---|---|
| `DB_PASSWORD` | PostgreSQL 비밀번호 | `strongPassword123` |
| `REDIS_PASSWORD` | Redis 비밀번호 | `redisPass456` |
| `CORS_ALLOWED_ORIGINS` | 허용할 프론트 주소 | `http://localhost:3000` |
| `WORKER1_IP` ~ `WORKER6_IP` | 워커 PC IP (운영 시) | `192.168.0.39` |

---

## 9. 배포 구조 (운영)

### 전체 배포 흐름

```
개발자 코드 push to main
        │
        ▼
GitHub Actions CI 실행
  ├── 단위 테스트 통과?
  ├── 통합 테스트 통과?
  └── Docker 빌드 성공?
        │ 모두 통과
        ▼
Self-hosted Runner (Master PC에서 실행)
  │
  ├── git pull (최신 코드)
  ├── docker compose -f docker-compose.master.yml up -d --build
  └── 헬스체크 확인 (최대 2분 대기)
        │
        ▼
Cloudflare Tunnel → 외부 사용자 접근 가능
```

### Self-hosted Runner 설치 (Master PC 최초 1회)

1. GitHub → 레포지토리 → **Settings** → **Actions** → **Runners**
2. **New self-hosted runner** 클릭
3. OS: Windows 선택
4. 화면에 나오는 명령어 복사해서 Master PC 터미널에 붙여넣기
5. 서비스로 등록: `./svc.sh install && ./svc.sh start`

### GitHub Secrets 등록 (Settings → Secrets → Actions)

| Secret 이름 | 값 |
|---|---|
| `DB_PASSWORD` | PostgreSQL 비밀번호 |
| `REDIS_PASSWORD` | Redis 비밀번호 |
| `CORS_ALLOWED_ORIGINS` | 실제 도메인 |
| `WORKER1_IP` ~ `WORKER6_IP` | 각 워커 PC 고정 IP |

### Master PC 수동 배포

```bash
cd MediCore
docker compose -f docker-compose.master.yml up -d --build
```

---

## 10. 워커 PC 세팅 방법

각 워커 PC 담당자가 수행합니다.

### Step 1 — 레포 클론 및 환경변수

```bash
git clone https://github.com/MadSadly/MediCore.git
cd MediCore
cp .env_example .env
```

`.env` 수정:
```env
DB_PASSWORD=팀장에게받은값       # Master PC PostgreSQL 비밀번호
MASTER_IP=192.168.0.39           # Master PC IP (변경 금지)
MODULE_NAME=skin                 # 본인 담당 질환으로 변경
```

### Step 2 — GCP 서비스 계정 키 준비

1. [Google Cloud Console](https://console.cloud.google.com) → **IAM & Admin** → **Service Accounts**
2. 서비스 계정 생성 → 역할: `Vertex AI User`
3. 키 생성 (JSON) → 다운로드
4. 키 파일을 `secrets/gcp-key.json` 경로에 저장

```bash
mkdir secrets
# 다운로드한 키 파일을 secrets/gcp-key.json 으로 복사
```

> ⚠️ `secrets/` 폴더는 `.gitignore`에 등록되어 있어 git에 올라가지 않습니다.

### Step 3 — 워커 서버 실행

```bash
docker compose -f docker-compose.worker.yml up -d
```

### Step 4 — 정상 확인

```bash
curl http://localhost:8000/health
# → {"status": "ok", "server": "FastAPI"}
```

### 워커 PC별 MODULE_NAME

| PC | 담당자 | MODULE_NAME | IP |
|---|---|---|---|
| Worker 1 | - | `skin` | 192.168.0.20 |
| Worker 2 | - | `brain` | 192.168.0.9 |
| Worker 3 | - | `eyes` | 192.168.0.32 |
| Worker 4 | - | `spine` | 192.168.0.13 |
| Worker 5 | - | `kidney` | 192.168.0.5 |
| Worker 6 | - | `colon` | 192.168.0.73 |

> IP는 공유기 설정에서 MAC 주소로 고정 IP 할당 필요

---

## 11. API 엔드포인트

### Spring Boot (`:8080`)

| Method | URL | 설명 |
|---|---|---|
| `GET` | `/actuator/health` | 서버 헬스체크 |
| `GET` | `/api/workers` | 전체 워커 PC 상태 조회 |
| `GET` | `/api/workers/{name}` | 특정 워커 상태 조회 |
| `PATCH` | `/api/workers/{name}/url?url=` | 워커 URL 변경 |

### FastAPI (`:8000`)

| Method | URL | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 헬스체크 |
| `GET` | `/ai/{module}/health` | 질환별 모듈 상태 |

### 워커 상태 예시 응답

```json
[
  {
    "name": "skin",
    "displayName": "피부 진단 서버",
    "url": "http://192.168.0.20:8000",
    "status": "HEALTHY",
    "circuitState": "CLOSED",
    "failCount": 0,
    "responseTimeMs": 23,
    "lastCheckedAt": "2026-04-23T11:00:00"
  }
]
```

---

## 12. 자주 묻는 질문 / 트러블슈팅

### Q. `run_all.bat` 실행 시 "Docker 실행 실패" 에러

→ Docker Desktop을 먼저 실행하세요. 트레이 아이콘에 고래 모양이 보여야 합니다.

### Q. Spring Boot가 뜨다가 DB 연결 에러로 죽음

→ `.env` 파일의 `DB_PASSWORD`가 비어있거나 틀린 경우입니다.  
→ `docker ps`로 `medizero-postgres`가 `healthy` 상태인지 확인하세요.

### Q. FastAPI 실행 시 `ModuleNotFoundError`

→ `AI/venv` 가상환경에 패키지가 설치되지 않은 상태입니다.
```bash
cd AI
venv\Scripts\activate
pip install -r requirements.txt
```

### Q. CI가 통합 테스트에서 실패함

→ `application-local.properties`의 DB 설정이 CI 환경과 맞지 않는 경우입니다.  
→ CI는 환경변수로 덮어쓰므로 `application-test.properties`가 올바른지 확인하세요.

### Q. 특정 워커가 OPEN 상태로 빠짐

→ 해당 워커 PC가 꺼져있거나 FastAPI가 다운된 상태입니다.  
→ `GET /api/workers`로 상태 확인 후 해당 워커 PC를 재시작하세요.  
→ 워커 복구 시 30초 이내에 자동으로 CLOSED 상태로 돌아옵니다.

### Q. 팀원 간 DB 데이터를 공유하고 싶어요

→ Supabase 무료 플랜 사용 권장 (pgvector 기본 지원).  
→ 연결 문자열을 `.env`의 `DB_PASSWORD`와 함께 공유하면 됩니다.

---

## 프로젝트 구조

```
MediCore/
├── .github/
│   └── workflows/
│       ├── ci.yml          ← 자동 테스트 (push/PR마다 실행)
│       └── deploy.yml      ← 자동 배포 (main push 시 실행)
│
├── backend-main/           ← Spring Boot
│   ├── Dockerfile
│   └── src/main/
│       ├── java/.../
│       │   ├── worker/     ← 워커 헬스체크 + Circuit Breaker
│       │   └── SecurityConfig.java  ← CORS 설정
│       └── resources/
│           ├── application.properties         ← 공통
│           ├── application-local.properties   ← 로컬 개발용
│           ├── application-prod.properties    ← 운영용 (env var)
│           ├── application-test.properties    ← CI 테스트용 (H2)
│           └── db/migration/
│               ├── V1__create_worker_nodes.sql
│               └── V2__create_medical_knowledge.sql
│
├── frontend/               ← React
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── DH/ GW/ MS/ NJ/ SH/ WJ/  ← 팀원별 작업 폴더
│       └── ...
│
├── AI/                     ← FastAPI
│   ├── Dockerfile
│   ├── main.py
│   ├── rag_engine.py       ← BGE-M3 + pgvector RAG
│   └── requirements.txt
│
├── nginx/
│   └── ai-lb.conf          ← AI 서버 로드밸런서 설정
│
├── postgres/
│   └── initdb.d/
│       └── 01_init.sql     ← pgvector 확장 초기화
│
├── docker-compose.yml          ← 로컬 개발용 (전체 스택)
├── docker-compose.master.yml   ← Master PC 운영용
├── docker-compose.worker.yml   ← Worker PC 운영용 (템플릿)
├── run_all.bat                 ← 로컬 개발 원클릭 실행
├── .env_example                ← 환경변수 템플릿
└── README.md
```