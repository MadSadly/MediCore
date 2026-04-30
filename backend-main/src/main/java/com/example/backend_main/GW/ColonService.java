package com.example.backend_main.GW;

import com.example.backend_main.GW.ColonResult;
import com.example.backend_main.GW.ColonResultRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Service
@RequiredArgsConstructor
public class ColonService {
    private final ColonResultRepository repository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    private static final String AI_SERVER_URL = "http://localhost:8000/ai/colon/diagnose";

    @Transactional
    public Map<String, Object> predictAndSave(String patientUid, Map<String, Object> inputs) throws Exception {
        // 1. AI 모델에 맞게 23개 피처로 확장 (사용자 입력 5개 + 기본값 18개)
        List<Object> features = new ArrayList<>();
        features.add(inputs.get("age"));                    // Age
        features.add("Male");                               // Gender (Default)
        features.add(inputs.get("cancerStage"));            // Cancer_Stage
        features.add(inputs.get("tumorSize"));              // Tumor_Size_mm
        features.add("No");                                 // Family_History
        features.add("No");                                 // Smoking_History
        features.add("No");                                 // Alcohol_Consumption
        features.add(inputs.get("bmi"));                    // Obesity_BMI
        features.add("Medium");                             // Diet_Risk
        features.add("Moderate");                           // Physical_Activity
        features.add(inputs.get("diabetes"));               // Diabetes
        features.add("No");                                 // IBD
        features.add("No");                                 // Genetic_Mutation
        features.add("No");                                 // Screening_History
        features.add("No");                                 // Early_Detection
        features.add("Surgery");                            // Treatment_Type
        features.add(5000);                                 // Healthcare_Costs
        features.add(20.5);                                 // Incidence_Rate
        features.add(10.2);                                 // Mortality_Rate
        features.add("Urban");                              // Urban_or_Rural
        features.add("Middle");                             // Economic
        features.add("High");                               // Access
        features.add("Yes");                                // Insurance

        // 2. AI 서버 호출
        Map<String, Object> aiRequest = new HashMap<>();
        aiRequest.put("features", features);
        
        Map<String, Object> aiResponse = restTemplate.postForObject(AI_SERVER_URL, aiRequest, Map.class);
        
        // 3. 결과 데이터 가공
        Integer prediction = Integer.parseInt(aiResponse.get("prediction").toString());
        Double probability = (Double) aiResponse.get("probability");
        String advice = (String) aiResponse.get("advice");

        // 4. DB 저장용 JSON 생성 (입력값 + 상담내역)
        Map<String, Object> storageMap = new HashMap<>(inputs);
        storageMap.put("advice", advice);
        String featuresJson = objectMapper.writeValueAsString(storageMap);

        // 5. DB 저장
        ColonResult result = ColonResult.builder()
                .patientUid(patientUid)
                .prediction(prediction)
                .probability(probability)
                .featuresJson(featuresJson)
                .build();
        repository.save(result);

        // 6. 응답 반환
        Map<String, Object> response = new HashMap<>();
        response.put("prediction", prediction);
        response.put("probability", probability);
        response.put("advice", advice);
        return response;
    }

    public List<ColonResult> getHistory(String patientUid) {
        return repository.findByPatientUidOrderByCreatedAtDesc(patientUid);
    }
}