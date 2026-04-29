package com.example.backend_main.SH.repository;

import com.example.backend_main.SH.entity.EyeDiagnosis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EyeDiagnosisRepository extends JpaRepository<EyeDiagnosis, Long> {

    List<EyeDiagnosis> findByPatientIdOrderByCreatedAtDesc(String patientId);
}
