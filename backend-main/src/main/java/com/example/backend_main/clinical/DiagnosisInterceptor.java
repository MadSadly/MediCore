package com.example.backend_main.clinical;

import com.example.backend_main.patient.PatientRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.time.LocalDate;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * POST /api/patients/{uid}/diagnoses 요청 완료 후
 * 해당 환자의 lastExamDate를 오늘로 자동 갱신.
 * diagnosis/* 패키지를 수정하지 않고 모든 모듈에 공통 적용.
 */
@Component
@RequiredArgsConstructor
public class DiagnosisInterceptor implements HandlerInterceptor {

    private static final Pattern DIAGNOSES_URI = Pattern.compile(
        "^/api/patients/([^/]+)/diagnoses$"
    );

    private final PatientRepository patientRepo;

    @Override
    public void afterCompletion(HttpServletRequest request,
                                HttpServletResponse response,
                                Object handler,
                                Exception ex) {
        if (!"POST".equalsIgnoreCase(request.getMethod())) return;
        if (response.getStatus() < 200 || response.getStatus() >= 300) return;

        Matcher m = DIAGNOSES_URI.matcher(request.getRequestURI());
        if (!m.matches()) return;

        String uid = m.group(1);
        patientRepo.findByUid(uid).ifPresent(p -> {
            p.setLastExamDate(LocalDate.now());
            patientRepo.save(p);
        });
    }
}