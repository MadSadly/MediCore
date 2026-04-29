package com.example.backend_main.NJ;

import com.example.backend_main.NJ.dto.KidneyDiagnosisRequest;
import com.example.backend_main.diagnosis.Diagnosis;
import com.example.backend_main.diagnosis.DiagnosisRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/patients/{patientUid}/diagnoses/kidney")
@RequiredArgsConstructor
public class KidneyDiagnosisController {

    private final DiagnosisRepository diagnosisRepository;
    private final ObjectMapper objectMapper;

    @PostMapping
    public ResponseEntity<Diagnosis> create(
            @PathVariable String patientUid,
            @RequestBody KidneyDiagnosisRequest req,
            Authentication auth
    ) throws JsonProcessingException {

        String resultJson = objectMapper.writeValueAsString(req);

        Diagnosis diagnosis = Diagnosis.builder()
                .patientUid(patientUid)
                .diseaseType("kidney")
                .title("신부전 진단: " + req.getResult())
                .summary(req.getDescription())
                .resultJson(resultJson)
                .createdBy(auth != null ? auth.getName() : null)
                .build();

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(diagnosisRepository.save(diagnosis));
    }
}
