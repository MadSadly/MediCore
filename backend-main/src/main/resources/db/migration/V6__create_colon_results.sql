-- 대장암 상담 결과 저장 테이블 (사용자 입력 데이터 포함)
CREATE TABLE colon_results (
    id BIGSERIAL PRIMARY KEY,
    patient_uid VARCHAR(50) NOT NULL,
    tumor_size_mm FLOAT,
    obesity_bmi VARCHAR(20),
    diabetes VARCHAR(5),
    ibd VARCHAR(5),
    genetic_mutation VARCHAR(50),
    prediction VARCHAR(10), -- Yes / No
    confidence FLOAT,
    advice TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_colon_results_patient_uid ON colon_results(patient_uid);