-- ================================================================
-- RAG 파이프라인용 의학 지식 벡터 테이블
-- BGE-M3 모델이 생성한 1024차원 벡터를 저장
-- ================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE medical_knowledge (
    id          BIGSERIAL PRIMARY KEY,
    content     TEXT         NOT NULL,          -- 문서 본문
    source      VARCHAR(500) NOT NULL,          -- 출처 (논문, 가이드라인 등)
    module_tag  VARCHAR(50)  NOT NULL,          -- 질환 태그 (격리 검색용)
                                                -- skin | brain | eyes | spine | kidney | colon
    embedding   VECTOR(1024) NOT NULL,          -- BGE-M3 임베딩 벡터
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 코사인 유사도 검색 성능을 위한 IVFFlat 인덱스
-- lists=100: 데이터 10만 건 기준 권장값
CREATE INDEX idx_medical_knowledge_embedding
    ON medical_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- module_tag 필터링 성능 인덱스
CREATE INDEX idx_medical_knowledge_module_tag
    ON medical_knowledge (module_tag);