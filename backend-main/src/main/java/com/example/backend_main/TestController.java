package com.example.backend_main;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class TestController {

    @Value("${ai.server.url}")
    private String aiServerUrl;

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "server", "Spring Boot");
    }

    @GetMapping("/ai-health")
    public Object aiHealth() {
        // Spring → FastAPI 연동 테스트
        return RestClient.create()
                .get()
                .uri(aiServerUrl + "/health")
                .retrieve()
                .body(Object.class);
    }
}
