package com.example.backend_main.hospital;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface HospitalStaffRepository extends JpaRepository<HospitalStaff, Long> {
    Optional<HospitalStaff> findByHospitalCodeAndEmployeeNumber(String hospitalCode, String employeeNumber);
}