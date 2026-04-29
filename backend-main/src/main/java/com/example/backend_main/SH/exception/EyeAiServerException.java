package com.example.backend_main.SH.exception;

import lombok.Getter;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.client.HttpStatusCodeException;

import java.nio.charset.StandardCharsets;

/**
 * AI 서버가 4xx/5xx와 본문(JSON 등)을 반환할 때 그대로 클라이언트에 전달하기 위한 예외
 */
@Getter
public class EyeAiServerException extends RuntimeException {

    private final HttpStatusCode statusCode;
    private final String responseBody;

    public EyeAiServerException(HttpStatusCode statusCode, String responseBody) {
        super("AI 서버 오류: " + statusCode);
        this.statusCode = statusCode;
        this.responseBody = responseBody != null ? responseBody : "";
    }

    public static EyeAiServerException from(HttpStatusCodeException ex) {
        String body = ex.getResponseBodyAsString(StandardCharsets.UTF_8);
        return new EyeAiServerException(ex.getStatusCode(), body);
    }
}
