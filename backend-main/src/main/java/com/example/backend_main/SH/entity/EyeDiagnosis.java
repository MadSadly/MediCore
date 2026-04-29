package com.example.backend_main.SH.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "eye_diagnoses")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EyeDiagnosis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String patientId;

    @Column(nullable = false)
    private String sessionId;

    // DL 결과
    @Column(nullable = false)
    private String primaryDisease;

    @Column(nullable = false)
    private Double confidence;

    private Integer stage;
    private String stageName;

    @Column(nullable = false)
    private Boolean isEmergency;

    private String emergencyReason;

    // GradCAM (Base64 — TEXT 컬럼)
    @Column(columnDefinition = "TEXT")
    private String gradcamBase64;

    // 소견서 (TEXT 컬럼)
    @Column(columnDefinition = "TEXT")
    private String report;

    // 메타
    private Double inferenceTimeMs;
    private Double qualityScore;

    @Column(nullable = false)
    private String modelVersion;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
