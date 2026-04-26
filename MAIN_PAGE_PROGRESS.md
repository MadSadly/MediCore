# feature/main-page 작업 내역

## 개요

브랜치 `feature/main-page`에서 MediCore AI 진단 플랫폼의 프론트엔드 공통 UI와 백엔드 인증/환자 API를 구현했습니다.

---

## Frontend

### 패키지 추가

```
react-router-dom ^7.14.2
```

### 파일 구조

```
frontend/src/
├── index.css                      # Tailwind v4 테마 토큰 + 공통 CSS
├── App.jsx                        # React Router 라우팅 설정
├── components/
│   ├── Sidebar.jsx                # 공통 사이드바 (토글 가능)
│   ├── Header.jsx                 # 공통 헤더
│   └── Layout.jsx                 # 인증 레이아웃 래퍼
└── pages/
    ├── LoginPage.jsx              # 로그인 / 회원가입 탭 전환
    ├── MainPage.jsx               # 메인 대시보드
    └── PatientDetailPage.jsx      # 환자 상세 분석 페이지
```

### 라우팅 구조

| 경로 | 컴포넌트 | 인증 필요 |
|---|---|---|
| `/login` | LoginPage | X |
| `/dashboard` | MainPage | O |
| `/patients/:id` | PatientDetailPage | O |
| `/brain-tumor` | ComingSoon | O |
| `/spine-disk` | ComingSoon | O |
| `/colon-cancer` | ComingSoon | O |
| `/kidney-failure` | ComingSoon | O |
| `/skin-disease` | ComingSoon | O |
| `/eye-disease` | ComingSoon | O |

> 각 팀원 담당 질환 경로는 `ComingSoon` placeholder로 연결되어 있습니다. 해당 경로에 각자 페이지를 붙이면 됩니다.

### 주요 기능

#### Sidebar (`components/Sidebar.jsx`)
- 7개 진단 모듈 + 설정/로그아웃 링크
- `◀ / ▶` 토글 버튼으로 **w-72 ↔ w-20** 전환
- 접힌 상태에서 아이콘만 표시, 마우스 호버 시 `title` 툴팁 제공
- 최근 분석 기록 2건 표시 (접히면 숨김)
- 로그아웃 시 localStorage 초기화 후 `/login` 이동

#### Header (`components/Header.jsx`)
- AI Diagnostics System 표기 + 페이지 제목
- 환자 이름/상태 배지 (선택적 props)
- 알림 벨 / 사용자 아바타 (이름 첫 글자)
- 환자 등록 버튼

#### Layout (`components/Layout.jsx`)
- `sidebarOpen` 상태를 보유하고 Sidebar와 메인 영역에 전달
- 사이드바 너비 변화에 따라 `marginLeft` 자동 조정 (`sidebar-transition` 애니메이션)
- `Outlet`으로 하위 라우트 렌더링

#### LoginPage (`pages/LoginPage.jsx`)
- **로그인 / 회원가입 탭** 전환 (같은 페이지)
- 이메일 + 비밀번호 유효성 검사
- 비밀번호 표시/숨김 토글
- 로그인 성공 시 JWT 토큰과 사용자 정보를 localStorage에 저장 후 `/dashboard` 이동
- 회원가입 성공 시 로그인 탭으로 자동 전환

#### MainPage (`pages/MainPage.jsx`)
- 환영 메시지 + 날짜/시스템 상태
- 통계 카드 4개 (총 분석 건수, 오늘 진단, 등록 환자, 평균 정확도)
- 진단 모듈 카드 6개 (클릭 시 해당 경로 이동)
- 최근 진단 환자 테이블 (클릭 시 `/patients/:id` 이동)

#### PatientDetailPage (`pages/PatientDetailPage.jsx`)
- **환자 프로필 카드** (UID, 나이, 성별, 혈액형, 최근 검사일)
- **진료 이력 타임라인** (날짜별 진료 기록, 활성/비활성 구분)
- **AI 분석 비교 리포트** (MRI 단면 이미지 영역, 성장 지수, 신뢰도, AI 인사이트 목록)
- PDF 리포트 생성 버튼
- **케이스 요약 카드** 3개 (안정성 점수, 복용 약물, 담당 의료팀)

### 디자인 시스템

Tailwind v4 `@theme` 블록으로 디자인 토큰 정의:

```css
--color-surface-lowest: #0b0e14   /* 최하단 배경 */
--color-primary-container: #2563eb /* 주요 강조색 (파란색) */
--color-on-surface: #e1e2eb        /* 본문 텍스트 */
```

공통 CSS 클래스:
- `.glass-card` — 반투명 다크 카드 (bg #0f172a + border #1e293b)
- `.ai-glow` — 파란 광채 테두리 (AI 분석 섹션)
- `.glow-blue` — 파란 버튼 그림자
- `.sidebar-transition` — 사이드바 너비 전환 애니메이션 (0.3s cubic-bezier)

---

## Backend

### 파일 구조

```
backend-main/src/main/java/com/example/backend_main/
├── SecurityConfig.java            # JWT 필터 + BCrypt + Stateless 세션
├── auth/
│   ├── JwtUtil.java               # JWT 생성/검증 (jjwt 0.12.6)
│   ├── JwtFilter.java             # 요청마다 Bearer 토큰 검증
│   ├── AuthService.java           # 회원가입/로그인 비즈니스 로직
│   ├── AuthController.java        # POST /api/auth/register, /login
│   └── dto/
│       ├── LoginRequest.java
│       ├── RegisterRequest.java
│       └── AuthResponse.java
├── user/
│   ├── User.java                  # users 테이블 엔티티
│   └── UserRepository.java
└── patient/
    ├── Patient.java               # patients 테이블 엔티티
    ├── PatientRepository.java
    └── PatientController.java     # GET /api/patients, GET /api/patients/{id}, POST
```

### 추가된 의존성 (`build.gradle`)

```gradle
implementation 'io.jsonwebtoken:jjwt-api:0.12.6'
runtimeOnly    'io.jsonwebtoken:jjwt-impl:0.12.6'
runtimeOnly    'io.jsonwebtoken:jjwt-jackson:0.12.6'
```

### API 엔드포인트

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| POST | `/api/auth/register` | X | 회원가입 |
| POST | `/api/auth/login` | X | 로그인 → JWT 반환 |
| GET | `/api/patients` | O | 환자 목록 조회 |
| GET | `/api/patients/{uid}` | O | 환자 상세 조회 |
| POST | `/api/patients` | O | 환자 등록 |

### 인증 흐름

```
클라이언트                     Spring Boot
    │  POST /api/auth/login        │
    │  { email, password }  ──────>│
    │                              │ BCrypt 검증
    │  { token, name, email } <────│ JWT 발급
    │                              │
    │  GET /api/patients           │
    │  Authorization: Bearer <token>─>│
    │                              │ JwtFilter 검증
    │  [ ...patients ]       <────│
```

### DB 마이그레이션 (Flyway)

| 파일 | 내용 |
|---|---|
| `V3__create_users.sql` | users 테이블 생성 |
| `V4__create_patients.sql` | patients 테이블 생성 + 샘플 환자 1건 |

### SecurityConfig 변경 사항

| 항목 | 이전 | 변경 후 |
|---|---|---|
| 세션 | 기본 (Stateful) | STATELESS |
| `/api/**` | 전체 허용 | JWT 인증 필요 |
| `/api/auth/**` | — | 인증 없이 허용 |
| 비밀번호 인코딩 | 없음 | BCryptPasswordEncoder |
| JWT 필터 | 없음 | JwtFilter 추가 |

### 환경 변수

`application.properties`에 추가된 설정:

```properties
jwt.secret=${JWT_SECRET:medicore-secret-key-must-be-at-least-256-bits-long-for-hs256}
jwt.expiration-ms=${JWT_EXPIRATION_MS:86400000}
```

> 프로덕션 배포 시 반드시 `JWT_SECRET` 환경 변수를 별도로 설정하세요.

---

## 각 팀원 연동 방법

각 팀원은 자신의 담당 경로에 페이지 컴포넌트를 작성하면 사이드바/헤더가 자동으로 적용됩니다.

예시 (피부질환 - 김민수):
```jsx
// frontend/src/MS/SkinDiseasePage.jsx
export default function SkinDiseasePage() {
  return <div>피부질환 분류 페이지</div>
}
```

`App.jsx`의 해당 라우트를 교체:
```jsx
// App.jsx
import SkinDiseasePage from './MS/SkinDiseasePage'
// ...
<Route path="skin-disease" element={<SkinDiseasePage />} />
```

---

*작업자: 김민수 / 브랜치: feature/main-page / 날짜: 2026-04-26*
