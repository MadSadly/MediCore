package com.example.backend_main.clinical;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "patient_status")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PatientStatus {

    @Id
    @Column(name = "patient_uid", length = 100)
    private String patientUid;

    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = "WAITING";

    @Column(nullable = false)
    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();
}