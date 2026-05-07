package com.example.backend_main.NJ;

import com.example.backend_main.NJ.dto.KidneyDiagnosisRequest;
import com.example.backend_main.diagnosis.Diagnosis;
import com.example.backend_main.diagnosis.DiagnosisRepository;
import com.example.backend_main.patient.PatientRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.*;

@RestController
@RequestMapping("/api/patients/{patientUid}/diagnoses/kidney")
@RequiredArgsConstructor
public class KidneyDiagnosisController {

    private final DiagnosisRepository diagnosisRepository;
    private final PatientRepository    patientRepository;

    @PostMapping
    public ResponseEntity<Diagnosis> create(
            @PathVariable String patientUid,
            @RequestBody KidneyDiagnosisRequest req,
            Authentication auth
    ) {
        ObjectMapper om = new ObjectMapper();
        Map<String, Object> resultMap = new LinkedHashMap<>();

        // 진단 결과
        resultMap.put("result",           req.getResult());
        resultMap.put("confidence",       req.getConfidence());
        resultMap.put("description",      req.getDescription());
        resultMap.put("severity",         req.getSeverity());
        resultMap.put("dialysisRequired", req.isDialysisRequired());
        if (req.getProbabilities() != null) resultMap.put("probabilities", req.getProbabilities());
        if (req.getRagAnswer()     != null) resultMap.put("ragAnswer",     req.getRagAnswer());

        // 환자 기본 정보
        if (req.getAge() != null) resultMap.put("age", req.getAge());
        if (req.getSex() != null) resultMap.put("sex", req.getSex());

        // 임상 수치
        if (req.getEgfr()  != null) resultMap.put("egfr",  req.getEgfr());
        if (req.getSc()    != null) resultMap.put("sc",    req.getSc());
        if (req.getBu()    != null) resultMap.put("bu",    req.getBu());
        if (req.getPot()   != null) resultMap.put("pot",   req.getPot());
        if (req.getAl()    != null) resultMap.put("al",    req.getAl());
        if (req.getBp()    != null) resultMap.put("bp",    req.getBp());
        if (req.getBgr()   != null) resultMap.put("bgr",   req.getBgr());
        if (req.getHemo()  != null) resultMap.put("hemo",  req.getHemo());

        // 동반 증상
        if (req.getHtn() != null) resultMap.put("htn", req.getHtn());
        if (req.getDm()  != null) resultMap.put("dm",  req.getDm());
        if (req.getPe()  != null) resultMap.put("pe",  req.getPe());

        String resultJson;
        try {
            resultJson = om.writeValueAsString(resultMap);
        } catch (Exception e) {
            resultJson = "{}";
        }

        Diagnosis diagnosis = Diagnosis.builder()
                .patientUid(patientUid)
                .diseaseType("kidney")
                .title("신부전 진단: " + req.getResult())
                .summary(req.getDescription())
                .resultJson(resultJson)
                .createdBy(auth != null ? auth.getName() : null)
                .build();

        Diagnosis saved = diagnosisRepository.save(diagnosis);

        // DiagnosisInterceptor는 /diagnoses/** 경로를 감청하지 않으므로 직접 갱신
        patientRepository.findByUid(patientUid).ifPresent(p -> {
            p.setLastExamDate(LocalDate.now());
            patientRepository.save(p);
        });

        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
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
            entry.put("id",        d.getId());
            entry.put("createdAt", d.getCreatedAt().toString());
            try {
                @SuppressWarnings("unchecked")
                Map<String, Object> json = om.readValue(d.getResultJson(), Map.class);
                entry.putAll(json);
            } catch (Exception e) {
                entry.put("result", null);
            }
            history.add(entry);
        }

        history.sort(Comparator.comparing(e -> (String) e.get("createdAt")));
        return ResponseEntity.ok(history);
    }
}
