package com.example.backend_main;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * 전체 Spring 컨텍스트 로드 통합 테스트.
 * CI integration job에서 SPRING_PROFILES_ACTIVE=local + 실제 PostgreSQL로 실행.
 */
@SpringBootTest
class ApplicationContextIntegrationTest {

	@Test
	void contextLoads() {
	}

}