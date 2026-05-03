package com.example.backend_main.DH;

import org.springframework.data.jpa.repository.JpaRepository;
import com.example.backend_main.DH.SpineDiagnosisHistory; // 엔티티 경로 확인

public interface SpineDiagnosisRepository extends JpaRepository<SpineDiagnosisHistory, Long> {
}