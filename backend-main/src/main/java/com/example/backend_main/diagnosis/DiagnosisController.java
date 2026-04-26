package com.example.backend_main.diagnosis;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/patients/{patientUid}/diagnoses")
@RequiredArgsConstructor
public class DiagnosisController {

    private final DiagnosisRepository diagnosisRepository;

    @GetMapping
    public List<Diagnosis> list(@PathVariable String patientUid) {
        return diagnosisRepository.findByPatientUidOrderByCreatedAtDesc(patientUid);
    }

    @PostMapping
    public ResponseEntity<Diagnosis> create(
            @PathVariable String patientUid,
            @RequestBody Diagnosis diagnosis
    ) {
        diagnosis.setPatientUid(patientUid);
        return ResponseEntity.status(HttpStatus.CREATED).body(diagnosisRepository.save(diagnosis));
    }
}