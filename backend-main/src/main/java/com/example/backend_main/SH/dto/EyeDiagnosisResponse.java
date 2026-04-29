package com.example.backend_main.SH.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class EyeDiagnosisResponse {

    private Long diagnosisId;
    private String patientId;
    private String sessionId;

    // DL 결과
    private String primaryDisease;
    private Double confidence;
    private Integer stage;
    private String stageName;
    private Boolean isEmergency;
    private String emergencyReason;

    // GradCAM
    private String gradcamBase64;

    // 소견서
    private String report;

    // 메타
    private Double inferenceTimeMs;
    private Double qualityScore;
    private String timestamp;
    private LocalDateTime createdAt;
}
