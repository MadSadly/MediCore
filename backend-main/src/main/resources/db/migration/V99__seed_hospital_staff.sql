CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO hospital_staff (hospital_code, employee_number, ssn_hash, license_number_hash, name, position, department)
VALUES
  ('HOSP001', 'EMP001', crypt('9001011234567', gen_salt('bf')), crypt('12345', gen_salt('bf')), '변운조', '전문의', '신경외과'),
  ('HOSP001', 'EMP002', crypt('9002022345678', gen_salt('bf')), crypt('22345', gen_salt('bf')), '김담현', '전문의', '정형외과'),
  ('HOSP001', 'EMP003', crypt('9003033456789', gen_salt('bf')), crypt('32345', gen_salt('bf')), '박기완', '전문의', '소화기내과'),
  ('HOSP001', 'EMP004', crypt('9004044567890', gen_salt('bf')), crypt('42345', gen_salt('bf')), '김남준', '전문의', '신장내과'),
  ('HOSP001', 'EMP005', crypt('9005055678901', gen_salt('bf')), crypt('52345', gen_salt('bf')), '김민수', '전문의', '피부과'),
  ('HOSP001', 'EMP006', crypt('9006066789012', gen_salt('bf')), crypt('62345', gen_salt('bf')), '홍승현', '전문의', '안과')
ON CONFLICT (hospital_code, employee_number) DO NOTHING;
