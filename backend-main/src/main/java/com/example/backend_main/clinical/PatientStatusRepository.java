package com.example.backend_main.clinical;

import org.springframework.data.jpa.repository.JpaRepository;

public interface PatientStatusRepository extends JpaRepository<PatientStatus, String> {
}