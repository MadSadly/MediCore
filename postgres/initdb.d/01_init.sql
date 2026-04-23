-- pgvector 확장 활성화 (RAG 파이프라인용)
CREATE EXTENSION IF NOT EXISTS vector;

-- 유사 문자열 검색용
CREATE EXTENSION IF NOT EXISTS pg_trgm;
