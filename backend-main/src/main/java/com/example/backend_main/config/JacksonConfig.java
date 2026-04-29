package com.example.backend_main.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

/**
 * Spring Boot 4 + {@code spring-boot-starter-webmvc} 테스트 컨텍스트 등에서
 * {@link ObjectMapper} 자동 구성이 없을 때 컨트롤러 주입이 실패하지 않도록 빈 제공.
 */
@Configuration
public class JacksonConfig {

    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }
}
