package com.medicore.dh;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@RestController
@RequestMapping("/api/analyze")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // React 로컬 테스트를 위한 CORS 허용
public class SpineDiagnosisController {

    private final SpineDiagnosisService spineDiagnosisService;

    @PostMapping("/spine")
    public ResponseEntity<?> analyzeSpine(
            @RequestParam("file") MultipartFile file,
            @RequestParam("clinicalData") String clinicalData) {

        try {
            log.info("요청 수신 - 파일명: {}, 문진데이터: {}", file.getOriginalFilename(), clinicalData);

            // Service 호출하여 분석 및 DB 저장 수행
            SpineDiagnosis result = spineDiagnosisService.analyzeAndSave(file, clinicalData);

            // React로 저장된 엔티티 정보(최종 결과) 반환
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            log.error("AI 척추 분석 중 오류 발생: ", e);
            return ResponseEntity.internalServerError().body("분석 실패: " + e.getMessage());
        }
    }
}