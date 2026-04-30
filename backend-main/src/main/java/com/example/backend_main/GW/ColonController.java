package com.example.backend_main.GW;

import com.example.backend_main.diagnosis.DiagnosisRequest;
import com.example.backend_main.diagnosis.DiagnosisService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

import java.util.Map;

@RestController
@RequestMapping("/api/gw/colon")
public class ColonController {

    private final WebClient webClient;
    private final DiagnosisService diagnosisService;

    @Value("${ai.server.url}")
    private String aiServerUrl;

    public ColonController(WebClient.Builder webClientBuilder, DiagnosisService diagnosisService) {
        this.webClient = webClientBuilder.baseUrl("http://localhost:8000").build(); // AI 서버 URL은 application.properties에서 설정
        this.diagnosisService = diagnosisService;
    }

    // AI 서버의 data_analysis 엔드포인트로 요청을 전달
    @PostMapping(value = "/data-analysis", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> analyzeData(@RequestPart("file") Flux<DataBuffer> file) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.asyncPart("file", file, DataBuffer.class).header("Content-Disposition", "form-data; name=file; filename=data.csv");

        return webClient.post()
                .uri(aiServerUrl + "/ai/colon/data_analysis")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .toEntity(String.class)
                .block();
    }

    // AI 서버의 model_training 엔드포인트로 요청을 전달
    @PostMapping(value = "/model-training", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> trainModel(@RequestPart("file") Flux<DataBuffer> file) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.asyncPart("file", file, DataBuffer.class).header("Content-Disposition", "form-data; name=file; filename=data.csv");

        return webClient.post()
                .uri(aiServerUrl + "/ai/colon/model_training")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .toEntity(String.class)
                .block();
    }

    // AI 서버의 predict 엔드포인트로 요청을 전달하고, 결과를 저장
    @PostMapping("/predict/{patientUid}")
    public ResponseEntity<DiagnosisRequest> predictAndSave(
            @PathVariable String patientUid,
            @RequestBody Map<String, Object> predictionRequest) {

        // AI 서버로 예측 요청
        ResponseEntity<Map> aiResponse = webClient.post()
                .uri(aiServerUrl + "/ai/colon/predict")
                .bodyValue(predictionRequest)
                .retrieve()
                .toEntity(Map.class)
                .block();

        // AI 예측 결과를 공통 진단 API를 통해 저장
        DiagnosisRequest diagnosisRequest = new DiagnosisRequest("colon-cancer", aiResponse.getBody().get("message").toString(), (Double) aiResponse.getBody().get("probability"));
        diagnosisRequest.setResultJson(aiResponse.getBody().toString());
        return ResponseEntity.ok(diagnosisService.saveDiagnosis(patientUid, diagnosisRequest));
    }
}