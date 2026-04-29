package com.example.backend_main.SH.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * 진단 이력 조회용 — {@code gradcamBase64}, {@code report} 제외
 */
@Getter
@Builder
public class EyeDiagnosisHistoryResponse {

    private Long diagnosisId;
    private String patientId;
    private String sessionId;

    private String primaryDisease;
    private Double confidence;
    private Integer stage;
    private String stageName;
    private Boolean isEmergency;
    private String emergencyReason;

    private Double inferenceTimeMs;
    private Double qualityScore;
    private LocalDateTime createdAt;
}
