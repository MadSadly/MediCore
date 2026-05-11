package com.example.backend_main.NJ;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface KidneyDiagnosisRepository extends JpaRepository<KidneyDiagnosis, Long> {

    List<KidneyDiagnosis> findByPatientUidOrderByCreatedAtDesc(String patientUid);
}
