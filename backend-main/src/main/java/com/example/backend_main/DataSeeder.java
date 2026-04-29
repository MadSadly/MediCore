package com.example.backend_main;

import com.example.backend_main.hospital.HospitalStaff;
import com.example.backend_main.hospital.HospitalStaffRepository;
import com.example.backend_main.patient.Patient;
import com.example.backend_main.patient.PatientRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.List;

/**
 * 개발/테스트 환경 전용 시드 데이터 삽입기.
 * spring.profiles.active=dev 일 때만 실행됩니다.
 */
@Slf4j
@Component
@Profile({"dev", "local"})
@RequiredArgsConstructor
public class DataSeeder implements ApplicationRunner {

    private final HospitalStaffRepository hospitalStaffRepository;
    private final PatientRepository        patientRepository;
    private final PasswordEncoder          passwordEncoder;

    @Override
    public void run(ApplicationArguments args) {
        seedHospitalStaff();
        seedPatients();
    }

    // ──────────────────────────── hospital_staff ────────────────────────────

    private void seedHospitalStaff() {
        if (hospitalStaffRepository.count() > 0) {
            log.info("[DataSeeder] hospital_staff 이미 존재 — 건너뜀");
            return;
        }

        // 테스트 계정 정보 (실제 운영에서는 이 파일을 사용하지 않음)
        // 주민번호/면허번호 평문 → BCrypt 해시로 저장
        List<HospitalStaff> staffList = List.of(
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP001")
                .ssnHash(passwordEncoder.encode("9001011234567"))   // 주민번호 평문
                .licenseNumberHash(passwordEncoder.encode("12345")) // 의사면허번호 평문
                .name("변운조")
                .phone("010-1111-0001")
                .position("전문의")
                .department("신경외과")
                .build(),
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP002")
                .ssnHash(passwordEncoder.encode("9002022345678"))
                .licenseNumberHash(passwordEncoder.encode("22345"))
                .name("김담현")
                .phone("010-1111-0002")
                .position("전문의")
                .department("정형외과")
                .build(),
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP003")
                .ssnHash(passwordEncoder.encode("9003033456789"))
                .licenseNumberHash(passwordEncoder.encode("32345"))
                .name("박기완")
                .phone("010-1111-0003")
                .position("전문의")
                .department("소화기내과")
                .build(),
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP004")
                .ssnHash(passwordEncoder.encode("9004044567890"))
                .licenseNumberHash(passwordEncoder.encode("42345"))
                .name("김남준")
                .phone("010-1111-0004")
                .position("전문의")
                .department("신장내과")
                .build(),
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP005")
                .ssnHash(passwordEncoder.encode("9005055678901"))
                .licenseNumberHash(passwordEncoder.encode("52345"))
                .name("김민수")
                .phone("010-1111-0005")
                .position("전문의")
                .department("피부과")
                .build(),
            HospitalStaff.builder()
                .hospitalCode("HOSP001")
                .employeeNumber("EMP006")
                .ssnHash(passwordEncoder.encode("9006066789012"))
                .licenseNumberHash(passwordEncoder.encode("62345"))
                .name("홍승현")
                .phone("010-1111-0006")
                .position("전문의")
                .department("안과")
                .build()
        );

        hospitalStaffRepository.saveAll(staffList);
        log.info("[DataSeeder] hospital_staff {}명 삽입 완료", staffList.size());
        log.info("[DataSeeder] 테스트 로그인 정보 — 병원코드: HOSP001 | 사원번호: EMP001~EMP006");
        log.info("[DataSeeder] 주민번호: 9001011234567(EMP001) ~ 9006066789012(EMP006)");
        log.info("[DataSeeder] 면허번호: 12345(EMP001) ~ 62345(EMP006)");
    }

    // ──────────────────────────────── patients ────────────────────────────────

    private void seedPatients() {
        if (patientRepository.count() > 1) {
            log.info("[DataSeeder] patients 이미 존재 — 건너뜀");
            return;
        }

        List<Patient> patients = List.of(
            patient("MED-0001", "김철수", 55, "남성", "A형 (Rh+)", "2024-11-10", "변운조",   "아스피린 100mg",     "종양학 유닛 A"),
            patient("MED-0002", "이영희", 43, "여성", "B형 (Rh+)", "2024-12-03", "김담현",   "이부프로펜 400mg",   "정형외과 팀"),
            patient("MED-0003", "박민준", 67, "남성", "O형 (Rh-)", "2025-01-15", "박기완",   "메트포르민 500mg",   "소화기 팀"),
            patient("MED-0004", "최수진", 38, "여성", "AB형 (Rh+)","2025-02-20", "김남준",   "에리스로포이에틴",    "신장 팀"),
            patient("MED-0005", "정대한", 51, "남성", "A형 (Rh-)", "2025-03-07", "김민수",   "트레티노인 0.05%",   "피부과 팀"),
            patient("MED-0006", "한지민", 29, "여성", "O형 (Rh+)", "2025-03-18", "홍승현",   "라니비주맙",         "안과 팀"),
            patient("MED-0007", "윤서준", 72, "남성", "B형 (Rh-)", "2025-01-29", "변운조",   "덱사메타손 4mg",     "신경외과 팀"),
            patient("MED-0008", "임나영", 46, "여성", "A형 (Rh+)", "2025-02-11", "김담현",   "세레콕시브 200mg",   "정형외과 팀"),
            patient("MED-0009", "오준혁", 60, "남성", "AB형 (Rh-)","2024-12-25", "박기완",   "옥살리플라틴",        "소화기종양 팀"),
            patient("MED-0010", "강예린", 34, "여성", "O형 (Rh+)", "2025-03-30", "김남준",   "타크로리무스 1mg",   "신장이식 팀"),
            patient("MED-9928", "아서 모건", 42, "남성", "O형 (Rh+)", "2023-10-24", "변운조", "덱사메타손",         "종양학 유닛 A")
        );

        patients.forEach(p -> {
            if (patientRepository.findByUid(p.getUid()).isEmpty()) {
                patientRepository.save(p);
            }
        });

        log.info("[DataSeeder] patients 삽입 완료");
    }

    private Patient patient(String uid, String name, int age, String gender,
                             String bloodType, String lastExam,
                             String doctor, String medication, String team) {
        return Patient.builder()
            .uid(uid)
            .name(name)
            .age(age)
            .gender(gender)
            .bloodType(bloodType)
            .lastExamDate(LocalDate.parse(lastExam))
            .assignedDoctor(doctor)
            .currentMedication(medication)
            .medicalTeam(team)
            .build();
    }
}
