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
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.nio.charset.StandardCharsets;
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
        String aiUrl = aiServerUrl + "/sh/analyze/sync";

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

        log.info("AI 서버 호출 시작 | url={} patientId={}", aiUrl, request.getPatientId());

        final ResponseEntity<Map<String, Object>> aiResponse;
        try {
            aiResponse = restTemplate.exchange(
                    aiUrl,
                    HttpMethod.POST,
                    entity,
                    new ParameterizedTypeReference<Map<String, Object>>() {}
            );
        } catch (HttpStatusCodeException ex) {
            log.error(
                    "AI 서버 HTTP 오류 | url={} patientId={} status={} responseBody={}",
                    aiUrl,
                    request.getPatientId(),
                    ex.getStatusCode(),
                    ex.getResponseBodyAsString(StandardCharsets.UTF_8),
                    ex
            );
            throw EyeAiServerException.from(ex);
        } catch (RestClientException ex) {
            log.error("AI 서버 연결 실패 | url={} patientId={}", aiUrl, request.getPatientId(), ex);
            throw new RuntimeException("AI 서버 연결 실패", ex);
        }

        if (!aiResponse.getStatusCode().is2xxSuccessful() || aiResponse.getBody() == null) {
            log.warn(
                    "AI 서버 응답 비정상 | url={} patientId={} status={}",
                    aiUrl,
                    request.getPatientId(),
                    aiResponse.getStatusCode()
            );
            throw new RuntimeException("AI 서버 응답 오류");
        }

        log.info(
                "AI 서버 응답 수신 | status={} patientId={}",
                aiResponse.getStatusCode(),
                request.getPatientId()
        );

        Map<String, Object> result = aiResponse.getBody();

        @SuppressWarnings("unchecked")
        Map<String, Object> dlResult =
                result.get("dl_result") instanceof Map ? (Map<String, Object>) result.get("dl_result") : null;
        if (dlResult == null) {
            throw new IllegalStateException("AI 응답에 dl_result가 없거나 형식이 올바르지 않습니다.");
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> primary =
                dlResult.get("primary_disease") instanceof Map
                        ? (Map<String, Object>) dlResult.get("primary_disease")
                        : null;
        if (primary == null) {
            throw new IllegalStateException("AI 응답에 primary_disease가 없습니다.");
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> stage =
                dlResult.get("stage") instanceof Map ? (Map<String, Object>) dlResult.get("stage") : null;

        String diseaseName =
                primary.get("disease_name") != null ? primary.get("disease_name").toString() : null;
        if (diseaseName == null || diseaseName.isBlank()) {
            throw new IllegalStateException("AI 응답 disease_name이 비어 있습니다.");
        }

        Object confObj = primary.get("confidence");
        if (!(confObj instanceof Number)) {
            throw new IllegalStateException("AI 응답 primary_disease.confidence가 없거나 숫자가 아닙니다.");
        }
        double confidence = ((Number) confObj).doubleValue();

        Object infObj = result.get("inference_time_ms");
        if (!(infObj instanceof Number)) {
            throw new IllegalStateException("AI 응답 inference_time_ms가 없거나 숫자가 아닙니다.");
        }
        double inferenceTimeMs = ((Number) infObj).doubleValue();

        Object sessionObj = result.get("session_id");
        String sessionId = sessionObj != null ? sessionObj.toString().trim() : "";
        if (sessionId.isEmpty()) {
            throw new IllegalStateException("AI 응답 session_id가 비어 있습니다.");
        }

        String report =
                result.get("report") != null ? result.get("report").toString() : "";

        String modelVersion =
                dlResult.get("model_version") != null
                        ? dlResult.get("model_version").toString()
                        : null;
        if (modelVersion == null || modelVersion.isBlank()) {
            modelVersion = "unknown";
        }

        String gradcam =
                dlResult.get("gradcam_base64") != null ? dlResult.get("gradcam_base64").toString() : null;

        @SuppressWarnings("unchecked")
        Map<String, Object> emergency =
                result.get("emergency") instanceof Map ? (Map<String, Object>) result.get("emergency") : null;
        boolean isEmergency = false;
        String emergencyReason = null;
        if (emergency != null) {
            Object ie = emergency.get("is_emergency");
            if (ie instanceof Boolean b) {
                isEmergency = b;
            } else if (ie != null) {
                isEmergency = Boolean.parseBoolean(ie.toString());
            }
            Object r = emergency.get("reason");
            emergencyReason = r != null ? r.toString() : null;
        }

        Double qualityScore =
                result.get("quality_score") instanceof Number
                        ? ((Number) result.get("quality_score")).doubleValue()
                        : null;

        EyeDiagnosis saved = repository.save(EyeDiagnosis.builder()
                .patientId(request.getPatientId())
                .sessionId(sessionId)
                .primaryDisease(diseaseName)
                .confidence(confidence)
                .stage(stage != null && stage.get("stage") instanceof Number
                        ? ((Number) stage.get("stage")).intValue()
                        : null)
                .stageName(
                        stage != null && stage.get("stage_name") != null
                                ? stage.get("stage_name").toString()
                                : null
                )
                .isEmergency(isEmergency)
                .emergencyReason(emergencyReason)
                .gradcamBase64(gradcam)
                .report(report)
                .inferenceTimeMs(inferenceTimeMs)
                .qualityScore(qualityScore)
                .modelVersion(modelVersion)
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
