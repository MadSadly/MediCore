-- V9__create_eye_diagnoses.sql
-- 안과 진단 결과 테이블 (SH 담당)
-- CLAUDE.md 규칙: V9 버전만 사용

CREATE TABLE IF NOT EXISTS eye_diagnoses (
    id                BIGSERIAL       PRIMARY KEY,
    patient_id        VARCHAR(100)    NOT NULL,
    session_id        VARCHAR(100)    NOT NULL,

    -- DL 진단 결과
    primary_disease   VARCHAR(50)     NOT NULL,
    confidence        DOUBLE PRECISION NOT NULL,
    stage             INTEGER,
    stage_name        VARCHAR(20),
    is_emergency      BOOLEAN         NOT NULL DEFAULT FALSE,
    emergency_reason  TEXT,

    -- GradCAM 히트맵 (Base64)
    gradcam_base64    TEXT,

    -- AI 소견서
    report            TEXT,

    -- 메타데이터
    inference_time_ms DOUBLE PRECISION,
    quality_score     DOUBLE PRECISION,
    model_version     VARCHAR(50)     NOT NULL DEFAULT 'swin_base_v1.0',

    created_at        TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_eye_diagnoses_patient_id
    ON eye_diagnoses (patient_id);

CREATE INDEX IF NOT EXISTS idx_eye_diagnoses_created_at
    ON eye_diagnoses (created_at DESC);

COMMENT ON TABLE eye_diagnoses IS '안과 AI 진단 결과 (module: eyes, SH 담당)';
