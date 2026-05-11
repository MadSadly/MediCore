-- V8__create_kidney_diagnoses.sql
-- 신부전 진단 결과 전용 테이블 (NJ 담당)

CREATE TABLE IF NOT EXISTS kidney_diagnoses (
    id                      BIGSERIAL           PRIMARY KEY,
    patient_uid             VARCHAR(50)         NOT NULL REFERENCES patients(uid) ON DELETE CASCADE,

    -- AI 진단 결과
    prediction              VARCHAR(20)         NOT NULL,   -- Normal, Stage1~Stage5
    confidence              DOUBLE PRECISION    NOT NULL,
    description             TEXT,
    severity                VARCHAR(20),                    -- low, moderate, high, critical
    dialysis_required       BOOLEAN             NOT NULL DEFAULT FALSE,

    -- 확률 분포 / 알림 / RAG (JSON)
    probabilities_json      TEXT,
    alerts_json             TEXT,
    rag_answer              TEXT,
    rag_sources_json        TEXT,
    feature_importance_json TEXT,

    -- 환자 기본 정보
    age                     DOUBLE PRECISION,
    sex                     VARCHAR(10),

    -- 수치형 임상 지표
    bp                      DOUBLE PRECISION,   -- 혈압 (mmHg)
    bgr                     DOUBLE PRECISION,   -- 혈당 (mg/dL)
    bu                      DOUBLE PRECISION,   -- BUN (mg/dL)
    sc                      DOUBLE PRECISION,   -- 크레아티닌 (mg/dL)
    sod                     DOUBLE PRECISION,   -- 나트륨 (mEq/L)
    pot                     DOUBLE PRECISION,   -- 칼륨 (mEq/L)
    hemo                    DOUBLE PRECISION,   -- 헤모글로빈 (g/dL)
    pcv                     DOUBLE PRECISION,   -- Packed Cell Volume (%)
    wc                      DOUBLE PRECISION,   -- 백혈구 수 (cells/cumm)
    rc                      DOUBLE PRECISION,   -- 적혈구 수 (millions/cmm)
    egfr                    DOUBLE PRECISION,   -- eGFR (mL/min/1.73m²)
    sg                      DOUBLE PRECISION,   -- 요비중
    al                      DOUBLE PRECISION,   -- 알부민 (g/dL)
    su                      DOUBLE PRECISION,   -- 요당 (mg/dL)

    -- 범주형 임상 지표
    rbc                     VARCHAR(20),        -- 요적혈구 (normal/abnormal)
    pc                      VARCHAR(20),        -- 농구세포 (normal/abnormal)
    pcc                     VARCHAR(20),        -- 농구세포 집락 (present/notpresent)
    ba                      VARCHAR(20),        -- 세균 (present/notpresent)
    htn                     VARCHAR(10),        -- 고혈압 (yes/no)
    dm                      VARCHAR(10),        -- 당뇨 (yes/no)
    cad                     VARCHAR(10),        -- 관상동맥질환 (yes/no)
    appet                   VARCHAR(10),        -- 식욕 (good/poor)
    pe                      VARCHAR(10),        -- 부종 (yes/no)
    ane                     VARCHAR(10),        -- 빈혈 (yes/no)

    -- 메타데이터
    created_by              VARCHAR(100),
    created_at              TIMESTAMP           NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_kidney_diagnoses_patient_uid
    ON kidney_diagnoses (patient_uid);

CREATE INDEX IF NOT EXISTS idx_kidney_diagnoses_created_at
    ON kidney_diagnoses (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_kidney_diagnoses_prediction
    ON kidney_diagnoses (prediction);

CREATE INDEX IF NOT EXISTS idx_kidney_diagnoses_egfr
    ON kidney_diagnoses (egfr);

COMMENT ON TABLE kidney_diagnoses IS '신부전 AI 진단 결과 (module: kidney, NJ 담당)';
