package com.example.backend_main.DH;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "spine_diagnosis_history")
@Getter
@Setter
public class SpineDiagnosisHistory {

    // 1. 기본키 (bigserial -> Long)
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "diagnosis_id")
    private Long id;

    // 2. 환자 ID (varchar(50))
    @Column(name = "patient_id", length = 50)
    private String patientId;

    // 3. MRI 이미지 경로 (varchar(255), not null)
    @Column(name = "mri_image_path", nullable = false)
    private String mriImagePath;

    // 4. 임상 증상 (jsonb, not null)
    // Hibernate 6 (Spring Boot 3.x 이상)의 최신 기능을 사용하여 JSONB를 Map으로 자동 변환합니다.
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "clinical_symptoms", nullable = false, columnDefinition = "jsonb")
    private String clinicalSymptoms;

    // 5. 딥러닝 비전 결과 (jsonb, not null)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "dl_vision_result", nullable = false, columnDefinition = "jsonb")
    private String dlVisionResult;

    // 6. LLM 의료 노트 (text, not null)
    @Column(name = "llm_medical_note", nullable = false, columnDefinition = "TEXT")
    private String llmMedicalNote;

    // 7. LLM 최종 리포트 (text, not null)
    @Column(name = "llm_final_report", nullable = false, columnDefinition = "TEXT")
    private String llmFinalReport;

    // 8. 생성일시 (timestamp default CURRENT_TIMESTAMP)
    @CreationTimestamp // 데이터를 삽입할 때 자동으로 현재 시간이 들어갑니다.
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
}