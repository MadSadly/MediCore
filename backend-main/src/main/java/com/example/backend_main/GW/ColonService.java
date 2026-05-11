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
        // 1. AI 모델 피처 매핑 (사용자 입력 5종 + 기본값 18종 = 총 23개)
        List<Object> features = new ArrayList<>();
        
        // Cancer Stage 문자열을 숫자로 변환 (모델 입력을 위한 전처리)
        Object rawStage = inputs.get("cancerStage");
        int stageNum = 1;
        if (rawStage != null) {
            if (rawStage.toString().contains("II")) stageNum = 2;
            if (rawStage.toString().contains("III")) stageNum = 3;
            if (rawStage.toString().contains("IV")) stageNum = 4;
        }

        features.add(inputs.get("age"));                    // 1. Age
        features.add("Male");                               // Gender (Default)
        features.add(stageNum);                             // 3. Cancer_Stage
        features.add(inputs.get("tumorSize"));              // 4. Tumor_Size_mm
        features.add("No");                                 // Family_History
        features.add("No");                                 // Smoking_History
        features.add("No");                                 // Alcohol_Consumption
        features.add(inputs.get("bmi"));                    // 8. Obesity_BMI
        features.add("Medium");                             // Diet_Risk
        features.add("Moderate");                           // Physical_Activity
        features.add(inputs.get("diabetes"));               // 11. Diabetes
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

        // 2. AI 서버(FastAPI) 호출하여 예측 수행
        Map<String, Object> aiRequest = new HashMap<>();
        aiRequest.put("features", features);
        
        Map<String, Object> aiResponse = restTemplate.postForObject(AI_SERVER_URL, aiRequest, Map.class);
        
        // 3. 결과 데이터 가공
        Integer prediction = Integer.parseInt(aiResponse.get("prediction").toString());
        Double probability = (Double) aiResponse.get("probability");
        String advice = (String) aiResponse.get("advice");

        // 4. 입력 내용, 사망률, 상담 내용을 하나의 JSON으로 통합 저장
        Map<String, Object> storageMap = new HashMap<>(inputs);
        storageMap.put("advice", advice);
        storageMap.put("mortalityRate", probability * 100); // 백분율 저장
        storageMap.put("predictedLabel", prediction == 1 ? "High Risk" : "Low Risk");
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