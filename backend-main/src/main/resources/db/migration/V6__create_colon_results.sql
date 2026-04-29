-- V6__create_colon_results.sql

CREATE TABLE colon_results (
    id          BIGSERIAL PRIMARY KEY,
    patient_uid VARCHAR(36) NOT NULL,
    prediction  INTEGER NOT NULL, -- 0: No Cancer, 1: Cancer
    probability FLOAT NOT NULL,
    features_json TEXT, -- 예측에 사용된 특성 데이터를 JSON 형태로 저장
    created_at  TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (patient_uid) REFERENCES patients(uid)
);