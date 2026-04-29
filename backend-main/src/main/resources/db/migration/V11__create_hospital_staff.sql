CREATE TABLE IF NOT EXISTS hospital_staff (
    id                   BIGSERIAL       PRIMARY KEY,
    hospital_code        VARCHAR(20)     NOT NULL,
    employee_number      VARCHAR(30)     NOT NULL,
    ssn_hash             VARCHAR(255)    NOT NULL,
    license_number_hash  VARCHAR(255),
    name                 VARCHAR(100)    NOT NULL,
    phone                VARCHAR(20),
    position             VARCHAR(50),
    department           VARCHAR(100),
    created_at           TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_hospital_staff UNIQUE (hospital_code, employee_number)
);

CREATE INDEX idx_hospital_staff_lookup ON hospital_staff(hospital_code, employee_number);

-- ※ 실제 데이터 삽입 방법:
--   ssn_hash, license_number_hash 는 반드시 BCrypt 해시값으로 저장해야 합니다.
--   Spring Boot 기동 후 /api/auth/hash?value=주민번호 (개발 전용 엔드포인트) 또는
--   BCryptPasswordEncoder().encode("값") 로 생성한 해시를 사용하세요.
--
-- 예시 INSERT (해시값은 실제 BCrypt 인코딩 결과로 교체 필요):
-- INSERT INTO hospital_staff
--     (hospital_code, employee_number, ssn_hash, license_number_hash, name, phone, position, department)
-- VALUES
--     ('HOSP001', 'EMP001', '{bcrypt_ssn_hash}', '{bcrypt_license_hash}', '홍길동', '010-0000-0000', '전문의', '피부과');