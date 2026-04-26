# Google Vertex AI 키 발급 가이드

> AI 서버에서 Gemini(LLM)를 사용하기 위한 GCP 서비스 계정 키 발급 방법입니다.
> 각자 본인 GCP 계정을 만들어서 사용합니다. (무료 크레딧 $300 제공)

---

## 1단계. GCP 계정 생성

1. https://cloud.google.com 접속
2. 우측 상단 **"무료로 시작하기"** 클릭
3. Google 계정으로 로그인
4. 국가: **대한민국** 선택
5. 카드 정보 입력 (무료 체험 기간 동안 **자동 결제 안 됨**, 본인이 유료 전환 안 하면 청구 없음)
6. 가입 완료 → **$300 크레딧** 자동 지급 (90일 유효)

---

## 2단계. GCP 프로젝트 생성

1. https://console.cloud.google.com 접속
2. 상단 메뉴바에서 프로젝트 선택 드롭다운 클릭 (예: "My First Project" 옆 화살표)
3. 우측 상단 **"새 프로젝트"** 클릭
4. 프로젝트 이름 입력: `medicore-본인이니셜` (예: `medicore-wj`)
5. **"만들기"** 클릭
6. 생성 후 상단 드롭다운에서 방금 만든 프로젝트 선택
7. 상단 드롭다운 옆 **프로젝트 ID** 복사해두기

> 프로젝트 이름(medicore-wj)과 프로젝트 ID는 다를 수 있음.
> `.env`에 넣어야 하는 건 **프로젝트 ID** 입니다.

---

## 3단계. Vertex AI API 활성화

1. 상단 검색창에 **"Vertex AI"** 입력
2. 검색 결과에서 **"Vertex AI"** 클릭
3. **"API 사용 설정"** (또는 "Enable") 버튼 클릭
4. 잠시 기다리면 활성화 완료

---

## 4단계. 서비스 계정 생성

1. 상단 검색창에 **"서비스 계정"** 입력 → **"서비스 계정"** 클릭
2. 상단 **"+ 서비스 계정 만들기"** 클릭
3. 아래 정보 입력:
   - 서비스 계정 이름: `medicore-ai`
   - 서비스 계정 ID: 자동 입력됨 (그대로 사용)
4. **"만들고 계속하기"** 클릭
5. 역할 선택 단계에서:
   - "역할 선택" 드롭다운 클릭
   - 검색창에 **"Vertex AI 사용자"** 입력
   - **"Vertex AI 사용자"** 선택
6. **"계속"** → **"완료"** 클릭

---

## 5단계. JSON 키 파일 다운로드

1. 서비스 계정 목록에서 방금 만든 `medicore-ai` 계정 클릭
2. 상단 탭에서 **"키"** 탭 클릭
3. **"키 추가"** → **"새 키 만들기"** 클릭
4. 키 유형: **JSON** 선택
5. **"만들기"** 클릭 → JSON 파일이 자동으로 다운로드됨

---

## 6단계. 키 파일 프로젝트에 저장

다운로드된 JSON 파일을 프로젝트 `secrets` 폴더에 넣기:

```cmd
mkdir C:\Users\본인이름\Desktop\MediCore\secrets
```

다운로드된 JSON 파일 이름을 `gcp-key.json` 으로 바꾼 뒤
`MediCore\secrets\` 폴더 안에 붙여넣기.

최종 경로 예시:
```
C:\Users\본인이름\Desktop\MediCore\secrets\gcp-key.json
```

> `secrets/` 폴더는 `.gitignore`에 등록되어 있어 절대 GitHub에 올라가지 않습니다.
> JSON 키 파일을 절대 다른 사람에게 공유하거나 GitHub에 올리지 마세요.

---

## 7단계. .env 파일에 등록

프로젝트 루트의 `.env` 파일을 메모장으로 열어서 아래 두 줄 수정:

```
GCP_PROJECT_ID=여기에_프로젝트_ID_입력
GCP_KEY_PATH=C:/Users/본인이름/Desktop/MediCore/secrets/gcp-key.json
```

> 경로는 **슬래시(/)** 또는 **역슬래시(\\\\)** 둘 다 사용 가능합니다.

---

## 확인 방법

AI 서버 실행 후 아래 로그가 뜨면 정상:

```
INFO: Vertex AI 초기화 완료 | 프로젝트: medicore-wj | 리전: asia-northeast3
```

에러가 뜨면:

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `GCP_PROJECT_ID 환경변수가 없습니다` | .env에 ID 미입력 | `.env` 파일 확인 |
| `Could not deserialize key data` | JSON 파일 경로 오류 | `GCP_KEY_PATH` 경로 재확인 |
| `PERMISSION_DENIED` | 역할 미설정 | 4단계에서 "Vertex AI 사용자" 역할 추가 |
| `API not enabled` | Vertex AI API 미활성화 | 3단계 재실행 |

---

## 요약

```
① cloud.google.com → 무료 계정 생성
② 콘솔 → 새 프로젝트 생성 → 프로젝트 ID 복사
③ Vertex AI API 활성화
④ 서비스 계정 생성 → 역할: Vertex AI 사용자
⑤ 키 탭 → JSON 키 다운로드
⑥ MediCore/secrets/gcp-key.json 으로 저장
⑦ .env 파일에 GCP_PROJECT_ID, GCP_KEY_PATH 입력
```
