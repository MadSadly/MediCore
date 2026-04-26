package com.example.backend_main.patient;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "patients")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Patient {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 50)
    private String uid;

    @Column(nullable = false, length = 100)
    private String name;

    private Integer age;

    @Column(length = 20)
    private String gender;

    @Column(length = 20)
    private String bloodType;

    private LocalDate lastExamDate;

    @Column(length = 100)
    private String assignedDoctor;

    @Column(length = 200)
    private String currentMedication;

    @Column(length = 200)
    private String medicalTeam;

    @Column(nullable = false, updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}