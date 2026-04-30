package com.example.backend_main.clinical;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
public class ClinicalWebMvcConfig implements WebMvcConfigurer {

    private final DiagnosisInterceptor diagnosisInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(diagnosisInterceptor)
                .addPathPatterns("/api/patients/*/diagnoses");
    }
}