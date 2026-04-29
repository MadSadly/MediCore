package com.example.backend_main.hospital;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(
    name = "hospital_staff",
    uniqueConstraints = @UniqueConstraint(columnNames = {"hospital_code", "employee_number"})
)
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class HospitalStaff {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "hospital_code", nullable = false, length = 20)
    private String hospitalCode;

    @Column(name = "employee_number", nullable = false, length = 30)
    private String employeeNumber;

    /** 주민등록번호 BCrypt 해시 */
    @Column(name = "ssn_hash", nullable = false, length = 255)
    private String ssnHash;

    /** 의사면허번호 BCrypt 해시 (선택) */
    @Column(name = "license_number_hash", length = 255)
    private String licenseNumberHash;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(length = 20)
    private String phone;

    @Column(length = 50)
    private String position;

    @Column(length = 100)
    private String department;

    @Column(nullable = false, updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}