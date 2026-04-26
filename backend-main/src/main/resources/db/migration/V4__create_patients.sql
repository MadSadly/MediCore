CREATE TABLE IF NOT EXISTS patients (
    id                  BIGSERIAL PRIMARY KEY,
    uid                 VARCHAR(50)   NOT NULL UNIQUE,
    name                VARCHAR(100)  NOT NULL,
    age                 INTEGER,
    gender              VARCHAR(20),
    blood_type          VARCHAR(20),
    last_exam_date      DATE,
    assigned_doctor     VARCHAR(100),
    current_medication  VARCHAR(200),
    medical_team        VARCHAR(200),
    created_at          TIMESTAMP     NOT NULL DEFAULT NOW()
);

INSERT INTO patients (uid, name, age, gender, blood_type, last_exam_date, assigned_doctor, current_medication, medical_team)
VALUES ('MED-9928', '아서 모건', 42, '남성', 'O형 (Rh+)', '2023-10-24', '변운조', '덱사메타손', '종양학 유닛 A')
ON CONFLICT (uid) DO NOTHING;
