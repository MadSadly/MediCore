-- V11__create_patient_status.sql
-- 환자 진료 상태 테이블 (MS 담당)
-- WAITING: 진료 대기 (AI 진단 가능), DONE: 진료 완료 (이력만 조회)

CREATE TABLE IF NOT EXISTS patient_status (
    patient_uid  VARCHAR(100) PRIMARY KEY,
    status       VARCHAR(20)  NOT NULL DEFAULT 'WAITING',
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 기존 환자 전원 WAITING 으로 초기화
INSERT INTO patient_status (patient_uid, status)
SELECT uid, 'WAITING' FROM patients
ON CONFLICT (patient_uid) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_patient_status_status
    ON patient_status (status);

COMMENT ON TABLE patient_status IS '환자 진료 상태 관리 (module: MS, WAITING/DONE)';
