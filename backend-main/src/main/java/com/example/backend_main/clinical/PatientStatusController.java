package com.example.backend_main.clinical;

import com.example.backend_main.patient.PatientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/patients")
@RequiredArgsConstructor
public class PatientStatusController {

    private final PatientStatusRepository statusRepo;
    private final PatientRepository       patientRepo;

    /** 단일 환자 상태 조회 */
    @GetMapping("/{uid}/status")
    public ResponseEntity<Map<String, String>> getStatus(@PathVariable String uid) {
        String status = statusRepo.findById(uid)
            .map(PatientStatus::getStatus)
            .orElseGet(() -> {
                statusRepo.save(PatientStatus.builder().patientUid(uid).build());
                return "WAITING";
            });
        return ResponseEntity.ok(Map.of("uid", uid, "status", status));
    }

    /** 전체 환자 상태 일괄 조회 — 메인페이지 통계 및 목록용 */
    @GetMapping("/statuses")
    public ResponseEntity<Map<String, String>> getAllStatuses() {
        Map<String, String> result = statusRepo.findAll().stream()
            .collect(Collectors.toMap(PatientStatus::getPatientUid, PatientStatus::getStatus));
        return ResponseEntity.ok(result);
    }

    /** 진단 저장 후 최근 검사일 자동 갱신 */
    @PatchMapping("/{uid}/last-exam-date")
    public ResponseEntity<Void> updateLastExamDate(@PathVariable String uid) {
        patientRepo.findByUid(uid).ifPresent(p -> {
            p.setLastExamDate(LocalDate.now());
            patientRepo.save(p);
        });
        return ResponseEntity.ok().build();
    }
}