-- users 테이블에 병원 소속 정보 추가
-- 병원코드 + 사원번호 조합으로 동일 직원 중복 가입 방지 (다병원 지원)

ALTER TABLE users
    ADD COLUMN hospital_code    VARCHAR(20),
    ADD COLUMN employee_number  VARCHAR(30);

-- 기존 데이터 보호를 위해 NULL 허용 후 UNIQUE 제약만 추가
-- 신규 가입자는 AuthService에서 반드시 두 값을 채워 저장
ALTER TABLE users
    ADD CONSTRAINT uq_users_hospital_employee
    UNIQUE (hospital_code, employee_number);
