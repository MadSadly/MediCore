package com.example.backend_main.SH.controller;

import com.example.backend_main.SH.exception.EyeAiServerException;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice(assignableTypes = EyeController.class)
public class EyeExceptionHandler {

    @ExceptionHandler(EyeAiServerException.class)
    public ResponseEntity<String> handleAiServerError(EyeAiServerException ex) {
        return ResponseEntity
                .status(ex.getStatusCode())
                .contentType(MediaType.APPLICATION_JSON)
                .body(ex.getResponseBody().isEmpty() ? "{}" : ex.getResponseBody());
    }
}
