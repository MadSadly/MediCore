package com.example.backend_main.diagnosis;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DiagnosisRepository extends JpaRepository<Diagnosis, Long> {
    List<Diagnosis> findByPatientUidOrderByCreatedAtDesc(String patientUid);
}