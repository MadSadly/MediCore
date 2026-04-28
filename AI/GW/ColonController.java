package com.example.backend_main.GW;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.util.Map;

@RestController
@RequestMapping("/api/gw/colon")
@RequiredArgsConstructor
public class ColonController {

    private final ColonResultRepository repository;
    private final RestTemplate restTemplate;

    @PostMapping("/diagnose")
    public Map<String, Object> diagnose(@RequestBody Map<String, Object> request) {
        // 1. AI 서버 호출
        String aiUrl = "http://ai-lb:8000/ai/colon/diagnose";
        Map<String, Object> aiRes = restTemplate.postForObject(aiUrl, request, Map.class);

        // 2. DB 저장 (상담 기록)
        ColonResultEntity entity = ColonResultEntity.builder()
                .patientUid((String) request.get("patient_uid"))
                .age((Integer) request.get("Age"))
                .gender((String) request.get("Gender"))
                .tumorSizeMm(Double.valueOf(request.get("Tumor_Size_mm").toString()))
                .prediction((String) aiRes.get("prediction"))
                .confidence((Double) aiRes.get("confidence"))
                .llmAdvice((String) aiRes.get("llm_advice"))
                .build();
        
        repository.save(entity);

        return aiRes;
    }
}