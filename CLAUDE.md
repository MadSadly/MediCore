# MediCore 프로젝트 규칙

## 먼저 확인할 것

세션 시작 시 반드시 사용자에게 물어보세요:
"이니셜이 무엇인가요? (WJ/DH/GW/MS/NJ/SH 중 하나)"

이니셜을 확인한 뒤 아래 규칙에 따라 해당 담당자의 폴더에서만 작업하세요.

---

## 팀원 담당 모듈

| 이니셜 | 담당 질환 | feature 브랜치 | DB 버전 | module명 |
|--------|----------|---------------|---------|---------|
| WJ | 뇌종양 진단 | feature/brain | V10 | brain |
| DH | 허리디스크 | feature/spine | V5 | spine |
| GW | 대장암 예측 | feature/colon | V6 | colon |
| MS | 피부질환 분류 | feature/skin | V7 | skin |
| NJ | 신부전 관리 | feature/kidney | V8 | kidney |
| SH | 안과질환 | feature/eyes | V9 | eyes |

---

## 작업 가능한 폴더 (이니셜 확인 후 해당 폴더만)

```
frontend/src/[이니셜]/         ← 프론트 페이지
backend-main/src/.../[이니셜]/ ← 백엔드 API
AI/[이니셜]/                   ← AI 모델 + RAG 엔진
```

---

## 절대 수정 금지 파일

아래 파일은 어떤 이유로도 수정하지 마세요.

**Frontend**
- `frontend/src/App.jsx`
- `frontend/src/components/*`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/MainPage.jsx`
- `frontend/src/pages/PatientDetailPage.jsx`
- `frontend/src/index.css`
- `frontend/package.json`

**Backend**
- `backend-main/src/.../SecurityConfig.java`
- `backend-main/src/.../auth/*`
- `backend-main/src/.../user/*`
- `backend-main/src/.../patient/*`
- `backend-main/src/.../worker/*`
- `backend-main/src/.../diagnosis/*`
- `backend-main/build.gradle`
- `backend-main/src/main/resources/application*.properties`

**AI**
- `AI/main.py`
- `AI/requirements.txt`

**DB**
- `backend-main/src/main/resources/db/migration/V1__*.sql` ~ `V4__*.sql`

---

## 백엔드 API 호출 (진단 결과 저장)

```javascript
POST /api/patients/{patientUid}/diagnoses
{
  "diseaseType": "brain-tumor",  // 본인 diseaseType
  "result": "...",
  "confidence": 0.95
}

GET /api/patients/{patientUid}/diagnoses
```

---

## DB 마이그레이션 (테이블 추가 필요 시)

본인 버전 번호로만 파일 생성. 다른 번호 절대 사용 금지.

```
backend-main/src/main/resources/db/migration/V[본인번호]__create_[테이블명].sql
```

---

## Vector DB (pgvector) 규칙

삽입 시 반드시 본인 module명으로 태깅:
```python
INSERT INTO medical_knowledge (module, content, embedding)
VALUES ('[본인module명]', '내용', [...])
```

조회 시 반드시 module 필터 포함:
```python
WHERE module = '[본인module명]'
```

필터 없이 전체 검색하면 다른 팀원 데이터와 섞여서 AI 환각 발생.

---

## AI 서버 엔드포인트 등록

`AI/[이니셜]/router.py` 파일이 이미 만들어져 있습니다.
`AI/main.py`는 건드리지 말고 본인 `router.py`에 엔드포인트만 추가하면 자동으로 서버에 연결됩니다.

---

## 커밋 전 확인 사항

- 본인 이니셜 폴더 외 파일이 변경되어 있으면 되돌리세요.
- `git diff --name-only`로 변경된 파일 목록 확인 후 커밋하세요.
- 커밋 메시지: 한국어로 작업 내용 간략히 작성.
