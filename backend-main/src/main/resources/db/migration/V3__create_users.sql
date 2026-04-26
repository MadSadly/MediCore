CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    email       VARCHAR(255)  NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,
    role        VARCHAR(50)   NOT NULL DEFAULT 'DOCTOR',
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW()
);
