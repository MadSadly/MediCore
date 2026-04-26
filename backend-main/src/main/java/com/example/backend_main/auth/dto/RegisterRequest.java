package com.example.backend_main.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;

@Getter
public class RegisterRequest {
    @NotBlank @Size(max = 100)
    private String name;
    @Email @NotBlank
    private String email;
    @NotBlank @Size(min = 8)
    private String password;
}