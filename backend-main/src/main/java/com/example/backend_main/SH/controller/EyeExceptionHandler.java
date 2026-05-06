package com.example.backend_main.SH.controller;

import com.example.backend_main.SH.exception.EyeAiServerException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@Slf4j
@RestControllerAdvice(assignableTypes = EyeController.class)
public class EyeExceptionHandler {

    @ExceptionHandler(EyeAiServerException.class)
    public ResponseEntity<String> handleAiServerError(EyeAiServerException ex) {
        return ResponseEntity
                .status(ex.getStatusCode())
                .contentType(MediaType.APPLICATION_JSON)
                .body(ex.getResponseBody().isEmpty() ? "{}" : ex.getResponseBody());
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String, String>> handleIllegalState(IllegalStateException ex) {
        log.error("안과 진단 필수 필드 또는 AI 응답 파싱 실패", ex);
        String msg = ex.getMessage() != null ? ex.getMessage() : "잘못된 요청";
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("error", msg));
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, String>> handleRuntime(RuntimeException ex) {
        log.error("안과 진단 서비스 런타임 오류", ex);
        String msg = ex.getMessage() != null ? ex.getMessage() : "내부 서버 오류";
        HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
        if (msg.startsWith("AI 서버 연결 실패")) {
            status = HttpStatus.SERVICE_UNAVAILABLE;
        }
        return ResponseEntity
                .status(status)
                .contentType(MediaType.APPLICATION_JSON)
                .body(Map.of("error", msg));
    }
}
