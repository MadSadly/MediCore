package com.example.backend_main.SH.service;

import com.example.backend_main.SH.dto.EyeDiagnosisHistoryResponse;
import com.example.backend_main.SH.dto.EyeDiagnosisRequest;
import com.example.backend_main.SH.dto.EyeDiagnosisResponse;
import com.example.backend_main.SH.entity.EyeDiagnosis;
import com.example.backend_main.SH.exception.EyeAiServerException;
import com.example.backend_main.SH.repository.EyeDiagnosisRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class EyeDiagnosisService {

    private final EyeDiagnosisRepository repository;
    private final RestTemplate restTemplate;

    @Value("${ai.server.url:http://localhost:8000}")
    private String aiServerUrl;

    /**
     * AI 서버(FastAPI)에 분석 요청 전송
     * 결과를 DB에 저장 후 응답 반환
     */
    public EyeDiagnosisResponse analyze(
            MultipartFile image,
            EyeDiagnosisRequest request,
            String authToken
    ) {
        String aiUrl = aiServerUrl + "/sh/analyze";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        headers.setBearerAuth(authToken);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", image.getResource());
        body.add("patient_id", request.getPatientId());
        body.add("patient_age", request.getPatientAge());
        body.add("has_diabetes", request.getHasDiabetes());
        body.add("has_hypertension", request.getHasHypertension());
        body.add("clinical_note", request.getClinicalNote());

        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);

        final ResponseEntity<Map> aiResponse;
        try {
            aiResponse = restTemplate.exchange(
                    aiUrl, HttpMethod.POST, entity, Map.class
            );
        } catch (HttpStatusCodeException ex) {
            throw EyeAiServerException.from(ex);
        }

        if (!aiResponse.getStatusCode().is2xxSuccessful() || aiResponse.getBody() == null) {
            throw new RuntimeException("AI 서버 응답 오류");
        }

        Map<String, Object> result = aiResponse.getBody();

        Map<String, Object> dlResult = (Map<String, Object>) result.get("dl_result");
        Map<String, Object> primary = (Map<String, Object>) dlResult.get("primary_disease");
        Map<String, Object> stage = (Map<String, Object>) dlResult.get("stage");
        Map<String, Object> emergency = (Map<String, Object>) result.get("emergency");

        EyeDiagnosis saved = repository.save(EyeDiagnosis.builder()
                .patientId(request.getPatientId())
                .sessionId((String) result.get("session_id"))
                .primaryDisease((String) primary.get("disease_name"))
                .confidence(((Number) primary.get("confidence")).doubleValue())
                .stage(stage != null ? (Integer) stage.get("stage") : null)
                .stageName(stage != null ? (String) stage.get("stage_name") : null)
                .isEmergency((Boolean) emergency.get("is_emergency"))
                .emergencyReason((String) emergency.get("reason"))
                .gradcamBase64((String) dlResult.get("gradcam_base64"))
                .report((String) result.get("report"))
                .inferenceTimeMs(((Number) result.get("inference_time_ms")).doubleValue())
                .qualityScore(result.get("quality_score") != null
                        ? ((Number) result.get("quality_score")).doubleValue() : null)
                .modelVersion((String) dlResult.get("model_version"))
                .build()
        );

        log.info("안과 진단 저장 완료 | patientId={} diagnosisId={}",
                request.getPatientId(), saved.getId());

        return EyeDiagnosisResponse.builder()
                .diagnosisId(saved.getId())
                .patientId(saved.getPatientId())
                .sessionId(saved.getSessionId())
                .primaryDisease(saved.getPrimaryDisease())
                .confidence(saved.getConfidence())
                .stage(saved.getStage())
                .stageName(saved.getStageName())
                .isEmergency(saved.getIsEmergency())
                .emergencyReason(saved.getEmergencyReason())
                .gradcamBase64(saved.getGradcamBase64())
                .report(saved.getReport())
                .inferenceTimeMs(saved.getInferenceTimeMs())
                .qualityScore(saved.getQualityScore())
                .timestamp((String) result.get("timestamp"))
                .createdAt(saved.getCreatedAt())
                .build();
    }

    /**
     * 환자 진단 이력 조회
     */
    public List<EyeDiagnosisHistoryResponse> getHistory(String patientId) {
        return repository.findByPatientIdOrderByCreatedAtDesc(patientId)
                .stream()
                .map(d -> EyeDiagnosisHistoryResponse.builder()
                        .diagnosisId(d.getId())
                        .patientId(d.getPatientId())
                        .sessionId(d.getSessionId())
                        .primaryDisease(d.getPrimaryDisease())
                        .confidence(d.getConfidence())
                        .stage(d.getStage())
                        .stageName(d.getStageName())
                        .isEmergency(d.getIsEmergency())
                        .emergencyReason(d.getEmergencyReason())
                        .inferenceTimeMs(d.getInferenceTimeMs())
                        .qualityScore(d.getQualityScore())
                        .createdAt(d.getCreatedAt())
                        .build()
                )
                .collect(Collectors.toList());
    }
}
