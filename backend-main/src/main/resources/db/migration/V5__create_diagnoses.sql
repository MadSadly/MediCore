CREATE TABLE IF NOT EXISTS diagnoses (
    id           BIGSERIAL     PRIMARY KEY,
    patient_uid  VARCHAR(50)   NOT NULL REFERENCES patients(uid) ON DELETE CASCADE,
    disease_type VARCHAR(50)   NOT NULL,
    title        VARCHAR(200)  NOT NULL,
    summary      TEXT,
    result_json  TEXT,
    created_by   VARCHAR(100),
    created_at   TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_diagnoses_patient_uid ON diagnoses(patient_uid);



