-- medical_knowledge 임베딩 모델 통일
-- BGE-M3 1024차원 → Gemini embedding-001 768차원
-- task_type 컬럼 추가 (RETRIEVAL_DOCUMENT | RETRIEVAL_QUERY)

-- 1. 기존 벡터 인덱스 제거 (차원 변경 전 필수)
DROP INDEX IF EXISTS idx_medical_knowledge_embedding;

-- 2. 기존 데이터 초기화 (차원이 달라 재임베딩 필요)
TRUNCATE TABLE medical_knowledge;

-- 3. 임베딩 컬럼을 768차원으로 변경
ALTER TABLE medical_knowledge
    ALTER COLUMN embedding TYPE vector(768);

-- 4. task_type 컬럼 추가
--    저장 시: RETRIEVAL_DOCUMENT
--    검색 시: RETRIEVAL_QUERY  (쿼리는 DB에 저장하지 않으므로 참고용)
ALTER TABLE medical_knowledge
    ADD COLUMN task_type VARCHAR(30) NOT NULL DEFAULT 'RETRIEVAL_DOCUMENT';

-- 5. 인덱스 재생성 (768차원 기준)
CREATE INDEX idx_medical_knowledge_embedding
    ON medical_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);