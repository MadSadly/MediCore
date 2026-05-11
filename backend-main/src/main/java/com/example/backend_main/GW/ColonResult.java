package com.example.backend_main.GW;

import lombok.*;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "colon_results")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class ColonResult {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "patient_uid", nullable = false)
    private String patientUid;

    @Column(nullable = false)
    private Integer prediction; // 0: 생존, 1: 사망위험

    @Column(nullable = false)
    private Double probability;

    @Column(name = "features_json", columnDefinition = "TEXT")
    private String featuresJson; // 입력값 + AI 상담내용 통합 저장

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}