package com.example.backend_main.SH.controller;

import com.example.backend_main.SH.dto.EyeDiagnosisHistoryResponse;
import com.example.backend_main.SH.dto.EyeDiagnosisRequest;
import com.example.backend_main.SH.dto.EyeDiagnosisResponse;
import com.example.backend_main.SH.service.EyeDiagnosisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/sh")
@RequiredArgsConstructor
public class EyeController {

    private final EyeDiagnosisService service;

    /**
     * 안과 AI 진단 요청
     * POST /api/sh/analyze
     */
    @PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<EyeDiagnosisResponse> analyze(
            @RequestParam("file") MultipartFile image,
            @RequestParam("patient_id") String patientId,
            @RequestParam(value = "patient_age", required = false) Integer patientAge,
            @RequestParam(value = "has_diabetes", defaultValue = "false") boolean hasDiabetes,
            @RequestParam(value = "has_hypertension", defaultValue = "false") boolean hasHypertension,
            @RequestParam(value = "clinical_note", required = false) String clinicalNote,
            @RequestHeader("Authorization") String authHeader
    ) {
        EyeDiagnosisRequest request = new EyeDiagnosisRequest();
        request.setPatientId(patientId);
        request.setPatientAge(patientAge);
        request.setHasDiabetes(hasDiabetes);
        request.setHasHypertension(hasHypertension);
        request.setClinicalNote(clinicalNote);

        String token = authHeader.replace("Bearer ", "");
        EyeDiagnosisResponse response = service.analyze(image, request, token);
        return ResponseEntity.ok(response);
    }

    /**
     * 환자 안과 진단 이력 조회
     * GET /api/sh/history/{patientId}
     */
    @GetMapping("/history/{patientId}")
    public ResponseEntity<List<EyeDiagnosisHistoryResponse>> getHistory(
            @PathVariable String patientId
    ) {
        return ResponseEntity.ok(service.getHistory(patientId));
    }
}
