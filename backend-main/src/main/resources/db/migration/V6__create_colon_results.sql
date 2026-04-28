-- 대장암 상담 결과 저장 테이블 (사용자 입력 데이터 포함)
CREATE TABLE colon_consultation_results (
    id              BIGSERIAL PRIMARY KEY,
    patient_uid     VARCHAR(50) NOT NULL,
    age             INT,
    gender          VARCHAR(1),
    tumor_size_mm   INT,
    cancer_stage    VARCHAR(10),
    treatment_type  VARCHAR(20),
    prediction      VARCHAR(10), -- 'Yes' or 'No'
    confidence      FLOAT,
    llm_advice      TEXT,        -- RAG + LLM 생성 답변
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_colon_consultation_results_patient_uid ON colon_consultation_results(patient_uid);