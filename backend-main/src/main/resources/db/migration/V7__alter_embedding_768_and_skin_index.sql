-- ================================================================
-- V7 (MS - 김민수): medical_knowledge embedding 차원 변경
-- BGE-M3 1024차원 → gemini-embedding-001 768차원 (팀 전체 합의)
-- ================================================================

-- 1. 기존 ivfflat 인덱스 제거 (차원 변경 전 필수)
DROP INDEX IF EXISTS idx_medical_knowledge_embedding;

-- 2. embedding 컬럼 타입 변경 1024 → 768
ALTER TABLE medical_knowledge
    ALTER COLUMN embedding TYPE VECTOR(768);

-- 3. 인덱스 재생성 (768차원 기준)
CREATE INDEX idx_medical_knowledge_embedding
    ON medical_knowledge
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
