package com.medicore.dh;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Service
@RequiredArgsConstructor
public class SpineDiagnosisService {

    private final SpineDiagnosisRepository repository;
    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Transactional
    public SpineDiagnosis analyzeAndSave(MultipartFile file, String clinicalData) throws Exception {
        // 1. Python AI 서버 주소 (FastAPI 라우터 설정에 맞춤)
        String aiServerUrl = "http://localhost:8000/api/dh/spine/analyze";

        // 2. HTTP 헤더 설정 (Multipart/form-data)
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        // 3. Body 데이터 구성 (MultiValueMap)
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        // MultipartFile을 RestTemplate으로 전송하기 위한 래핑 처리
        ByteArrayResource fileAsResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename(); // 파일명을 명시해야 Python에서 정상 인식
            }
        };

        body.add("file", fileAsResource);
        body.add("clinicalData", clinicalData);

        // 4. Python 서버로 POST 요청
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
        log.info("🚀 Python AI 서버로 분석 요청 중...");

        ResponseEntity<AiResponseDto> response = restTemplate.postForEntity(
                aiServerUrl,
                requestEntity,
                AiResponseDto.class
        );

        AiResponseDto aiResult = response.getBody();
        if (aiResult == null) {
            throw new RuntimeException("AI 서버로부터 빈 응답을 받았습니다.");
        }

        log.info("✅ AI 분석 완료 및 응답 수신 성공!");

        // 5. DB 엔티티 생성 및 데이터 매핑
        SpineDiagnosis diagnosis = new SpineDiagnosis();

        // 이미지 저장 로직이 있다면 여기서 S3 URL 등을 매핑 (현재는 파일명으로 임시 대체)
        diagnosis.setImageUrl(file.getOriginalFilename());

        // JsonNode를 String으로 변환하여 DB에 저장
        diagnosis.setVisionAnalysisJson(objectMapper.writeValueAsString(aiResult.getVisionAnalysis()));
        diagnosis.setClinicalDataJson(clinicalData);
        diagnosis.setMedicalNote(aiResult.getMedicalNote());
        diagnosis.setFinal_report(aiResult.getFinalReport());

        // 6. DB에 최종 저장 (JPA save)
        return repository.save(diagnosis);
    }
}