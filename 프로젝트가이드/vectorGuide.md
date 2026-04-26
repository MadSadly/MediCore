# Vector DB (pgvector) 사용 가이드

---

## pgvector가 뭔가요?

PostgreSQL 안에 있는 확장 기능이에요. 일반 RDB랑 같은 DB인데 **벡터(숫자 배열)를 저장하고 유사도 검색**을 할 수 있어요.

```
PostgreSQL (같은 DB)
  ├── 일반 테이블  → 환자정보, 진단결과 등 텍스트/숫자로 저장
  └── pgvector 테이블 → 의학 지식 문서를 임베딩 변환 후 벡터로 저장
```

---

## 왜 module 태깅이 필요한가?

벡터 DB에 전체 팀이 데이터를 넣다 보면 뇌종양, 피부, 신장 등 **모든 데이터가 섞여서 저장**돼요.

이 상태에서 뇌종양 AI가 "두통이 심한데요" 라는 질문에 답할 때 피부나 신장 관련 문서까지 검색되면 **엉뚱한 답변(환각)이 생성**될 수 있어요.

module 태깅으로 각 AI 서버가 **본인 담당 데이터만 읽도록** 강제해야 해요.

---

## 테이블 구조

```sql
CREATE TABLE medical_knowledge (
    id        SERIAL PRIMARY KEY,
    module    VARCHAR(20),    -- 담당 모듈명 (아래 목록 참고)
    content   TEXT,           -- 원본 텍스트
    embedding vector(1024)    -- BGE-M3 임베딩 벡터
);

-- 조회 성능을 위한 인덱스
CREATE INDEX ON medical_knowledge (module);
CREATE INDEX ON medical_knowledge USING ivfflat (embedding vector_cosine_ops);
```

---

## 담당 module 이름 (반드시 이 이름으로 통일)

| 담당 | module 값 |
|------|-----------|
| 뇌종양 | `brain` |
| 피부 | `skin` |
| 안과 | `eyes` |
| 척추 | `spine` |
| 신장 | `kidney` |
| 대장암 | `colon` |

> **오타 주의.** module 값이 다르면 조회가 안 됩니다.

---

## 데이터 삽입 규칙

### 흐름

```
의학 문서 텍스트
      ↓
BGE-M3 임베딩 모델로 변환
      ↓
[0.12, -0.34, 0.87, ...]  (1024개 숫자)
      ↓
module 태깅 후 PostgreSQL에 저장
```

### 코드 예시

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

def insert_knowledge(db_conn, module: str, text: str):
    embedding = model.encode(text)['dense_vecs']

    db_conn.execute("""
        INSERT INTO medical_knowledge (module, content, embedding)
        VALUES (%s, %s, %s)
    """, (module, text, embedding.tolist()))
```

### 삽입 시 주의사항

- **본인 담당 module 값만 사용할 것**
- 다른 팀원 module로 넣지 말 것
- 텍스트 원본도 같이 저장해야 LLM이 읽을 수 있음

---

## 데이터 조회 규칙

### 흐름

```
사용자 질문
      ↓
BGE-M3로 질문도 임베딩 변환
      ↓
본인 module 필터 + 벡터 유사도 검색
      ↓
가장 유사한 문서 N개 반환 → LLM에 전달
```

### 코드 예시

```python
def search_knowledge(db_conn, module: str, query: str, top_k: int = 5):
    query_embedding = model.encode(query)['dense_vecs']

    results = db_conn.execute("""
        SELECT content
        FROM medical_knowledge
        WHERE module = %s
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (module, query_embedding.tolist(), top_k))

    return [row[0] for row in results]
```

### 조회 시 주의사항

- **WHERE module = %s 필터를 반드시 포함할 것**
- 필터 없이 조회하면 전체 데이터 검색 → 환각 발생
- top_k는 5개 내외 권장 (너무 많으면 LLM 컨텍스트 초과)

---

## 요약

| 규칙 | 내용 |
|------|------|
| 삽입 | 반드시 본인 module 값으로 태깅 |
| 조회 | 반드시 WHERE module = '본인모듈' 필터 포함 |
| 임베딩 모델 | BGE-M3 통일 (다른 모델 쓰면 벡터 차원 달라짐) |
| 벡터 차원 | 1024 고정 |
