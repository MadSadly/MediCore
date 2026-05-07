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

    private final DiagnosisRepository       diagnosisRepository;
    private final KidneyDiagnosisRepository kidneyDiagnosisRepository;
    private final PatientRepository         patientRepository;

    @PostMapping
    public ResponseEntity<Diagnosis> create(
            @PathVariable String patientUid,
            @RequestBody KidneyDiagnosisRequest req,
            Authentication auth
    ) {
        ObjectMapper om = new ObjectMapper();
        String createdBy = auth != null ? auth.getName() : null;

        // ── 1. 공통 diagnoses 테이블 저장 ──────────────────────────────────
        Map<String, Object> resultMap = new LinkedHashMap<>();
        resultMap.put("result",           req.getResult());
        resultMap.put("confidence",       req.getConfidence());
        resultMap.put("description",      req.getDescription());
        resultMap.put("severity",         req.getSeverity());
        resultMap.put("dialysisRequired", req.isDialysisRequired());
        if (req.getProbabilities() != null) resultMap.put("probabilities", req.getProbabilities());
        if (req.getRagAnswer()     != null) resultMap.put("ragAnswer",     req.getRagAnswer());
        if (req.getAge()           != null) resultMap.put("age",           req.getAge());
        if (req.getSex()           != null) resultMap.put("sex",           req.getSex());
        if (req.getEgfr()          != null) resultMap.put("egfr",          req.getEgfr());
        if (req.getSc()            != null) resultMap.put("sc",            req.getSc());
        if (req.getBu()            != null) resultMap.put("bu",            req.getBu());
        if (req.getPot()           != null) resultMap.put("pot",           req.getPot());
        if (req.getAl()            != null) resultMap.put("al",            req.getAl());
        if (req.getBp()            != null) resultMap.put("bp",            req.getBp());
        if (req.getBgr()           != null) resultMap.put("bgr",           req.getBgr());
        if (req.getHemo()          != null) resultMap.put("hemo",          req.getHemo());
        if (req.getHtn()           != null) resultMap.put("htn",           req.getHtn());
        if (req.getDm()            != null) resultMap.put("dm",            req.getDm());
        if (req.getPe()            != null) resultMap.put("pe",            req.getPe());

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
                .createdBy(createdBy)
                .build();

        Diagnosis saved = diagnosisRepository.save(diagnosis);

        // ── 2. kidney_diagnoses 전용 테이블 저장 ───────────────────────────
        try {
            KidneyDiagnosis detail = KidneyDiagnosis.builder()
                    .patientUid(patientUid)
                    .prediction(req.getResult())
                    .confidence(req.getConfidence())
                    .description(req.getDescription())
                    .severity(req.getSeverity())
                    .dialysisRequired(req.isDialysisRequired())
                    .probabilitiesJson(req.getProbabilities() != null
                            ? om.writeValueAsString(req.getProbabilities()) : null)
                    .ragAnswer(req.getRagAnswer())
                    .age(req.getAge())
                    .sex(req.getSex())
                    .bp(req.getBp())
                    .bgr(req.getBgr())
                    .bu(req.getBu())
                    .sc(req.getSc())
                    .sod(req.getSod())
                    .pot(req.getPot())
                    .hemo(req.getHemo())
                    .pcv(req.getPcv())
                    .wc(req.getWc())
                    .rc(req.getRc())
                    .egfr(req.getEgfr())
                    .sg(req.getSg())
                    .al(req.getAl())
                    .su(req.getSu())
                    .rbc(req.getRbc())
                    .pc(req.getPc())
                    .pcc(req.getPcc())
                    .ba(req.getBa())
                    .htn(req.getHtn())
                    .dm(req.getDm())
                    .cad(req.getCad())
                    .appet(req.getAppet())
                    .pe(req.getPe())
                    .ane(req.getAne())
                    .createdBy(createdBy)
                    .build();
            kidneyDiagnosisRepository.save(detail);
        } catch (Exception e) {
            // 전용 테이블 저장 실패 시 공통 테이블 저장 결과는 유지
        }

        // ── 3. 최근 검사일 갱신 ────────────────────────────────────────────
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
        List<KidneyDiagnosis> records =
                kidneyDiagnosisRepository.findByPatientUidOrderByCreatedAtDesc(patientUid);

        List<Map<String, Object>> history = new ArrayList<>();
        for (KidneyDiagnosis d : records) {
            Map<String, Object> entry = new LinkedHashMap<>();
            entry.put("id",               d.getId());
            entry.put("createdAt",        d.getCreatedAt().toString());
            entry.put("result",           d.getPrediction());
            entry.put("confidence",       d.getConfidence());
            entry.put("description",      d.getDescription());
            entry.put("severity",         d.getSeverity());
            entry.put("dialysisRequired", d.getDialysisRequired());
            entry.put("ragAnswer",        d.getRagAnswer());
            entry.put("age",              d.getAge());
            entry.put("sex",              d.getSex());
            entry.put("egfr",             d.getEgfr());
            entry.put("sc",               d.getSc());
            entry.put("bu",               d.getBu());
            entry.put("pot",              d.getPot());
            entry.put("hemo",             d.getHemo());
            entry.put("bp",               d.getBp());
            entry.put("bgr",              d.getBgr());
            entry.put("htn",              d.getHtn());
            entry.put("dm",               d.getDm());
            entry.put("pe",               d.getPe());
            history.add(entry);
        }

        return ResponseEntity.ok(history);
    }
}
