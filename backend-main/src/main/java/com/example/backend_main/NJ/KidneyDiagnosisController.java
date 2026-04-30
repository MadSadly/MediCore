package com.example.backend_main.NJ;

import com.example.backend_main.NJ.dto.KidneyDiagnosisRequest;
import com.example.backend_main.diagnosis.Diagnosis;
import com.example.backend_main.diagnosis.DiagnosisRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/patients/{patientUid}/diagnoses/kidney")
@RequiredArgsConstructor
public class KidneyDiagnosisController {

    private final DiagnosisRepository diagnosisRepository;

    @PostMapping
    public ResponseEntity<Diagnosis> create(
            @PathVariable String patientUid,
            @RequestBody KidneyDiagnosisRequest req,
            Authentication auth
    ) {
        String egfrPart = req.getEgfr() != null
                ? String.format(",\"egfr\":%.1f", req.getEgfr())
                : "";

        String resultJson = String.format(
            "{\"result\":\"%s\",\"confidence\":%.4f,\"description\":\"%s\",\"severity\":\"%s\",\"dialysisRequired\":%b%s}",
            req.getResult(), req.getConfidence(), req.getDescription(),
            req.getSeverity(), req.isDialysisRequired(), egfrPart
        );

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

    @GetMapping("/history")
    public ResponseEntity<List<Map<String, Object>>> getHistory(
            @PathVariable String patientUid
    ) {
        List<Diagnosis> all = diagnosisRepository.findByPatientUidOrderByCreatedAtDesc(patientUid);
        ObjectMapper om = new ObjectMapper();
        List<Map<String, Object>> history = new ArrayList<>();

        for (Diagnosis d : all) {
            if (!"kidney".equals(d.getDiseaseType())) continue;
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("id", d.getId());
            entry.put("createdAt", d.getCreatedAt().toString());
            try {
                Map<?, ?> json = om.readValue(d.getResultJson(), Map.class);
                entry.put("egfr", json.get("egfr"));
                entry.put("result", json.get("result"));
            } catch (Exception e) {
                entry.put("egfr", null);
                entry.put("result", null);
            }
            history.add(entry);
        }

        history.sort(Comparator.comparing(e -> (String) e.get("createdAt")));
        return ResponseEntity.ok(history);
    }
}
