package com.example.backend_main.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;

@Getter
public class RegisterRequest {

    @NotBlank @Size(max = 20)
    private String hospitalCode;

    @NotBlank @Size(max = 30)
    private String employeeNumber;

    /** 주민등록번호 또는 의사면허번호 */
    @NotBlank
    private String ssnOrLicense;

    @Email @NotBlank
    private String email;

    @NotBlank @Size(min = 8)
    private String password;
}