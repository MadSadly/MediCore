package com.example.backend_main.NJ;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "kidney_diagnoses")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class KidneyDiagnosis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "patient_uid", nullable = false, length = 50)
    private String patientUid;

    // AI 진단 결과
    @Column(nullable = false, length = 20)
    private String prediction;

    @Column(nullable = false)
    private Double confidence;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(length = 20)
    private String severity;

    @Column(name = "dialysis_required", nullable = false)
    @Builder.Default
    private Boolean dialysisRequired = false;

    // JSON 저장 필드
    @Column(name = "probabilities_json", columnDefinition = "TEXT")
    private String probabilitiesJson;

    @Column(name = "alerts_json", columnDefinition = "TEXT")
    private String alertsJson;

    @Column(name = "rag_answer", columnDefinition = "TEXT")
    private String ragAnswer;

    @Column(name = "rag_sources_json", columnDefinition = "TEXT")
    private String ragSourcesJson;

    @Column(name = "feature_importance_json", columnDefinition = "TEXT")
    private String featureImportanceJson;

    // 환자 기본 정보
    private Double age;

    @Column(length = 10)
    private String sex;

    // 수치형 임상 지표
    private Double bp;
    private Double bgr;
    private Double bu;
    private Double sc;
    private Double sod;
    private Double pot;
    private Double hemo;
    private Double pcv;
    private Double wc;
    private Double rc;
    private Double egfr;
    private Double sg;
    private Double al;
    private Double su;

    // 범주형 임상 지표
    @Column(length = 20)
    private String rbc;

    @Column(length = 20)
    private String pc;

    @Column(length = 20)
    private String pcc;

    @Column(length = 20)
    private String ba;

    @Column(length = 10)
    private String htn;

    @Column(length = 10)
    private String dm;

    @Column(length = 10)
    private String cad;

    @Column(length = 10)
    private String appet;

    @Column(length = 10)
    private String pe;

    @Column(length = 10)
    private String ane;

    // 메타데이터
    @Column(name = "created_by", length = 100)
    private String createdBy;

    @Column(name = "created_at", nullable = false, updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @PrePersist
    private void prePersist() {
        if (createdAt == null) createdAt = LocalDateTime.now();
    }
}
