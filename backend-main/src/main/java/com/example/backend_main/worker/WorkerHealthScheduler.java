package com.example.backend_main.worker;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 워커 PC 헬스체크 스케줄러
 *
 * 5초마다 모든 워커 PC의 /health 엔드포인트를 호출하여 상태를 DB에 기록.
 * Circuit Breaker 패턴으로 장애 워커를 자동 차단/복구함.
 *
 * [Circuit Breaker 상태 전이]
 * CLOSED → (연속 3회 실패) → OPEN → (30초 후) → HALF_OPEN → (성공) → CLOSED
 *                                                              → (실패) → OPEN
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class WorkerHealthScheduler {

    private final WorkerNodeRepository workerNodeRepository;

    private static final int TIMEOUT_MS = 3000;

    private final RestClient restClient = RestClient.builder()
            .requestFactory(timeoutFactory())
            .defaultHeader("Content-Type", "application/json")
            .build();

    private static SimpleClientHttpRequestFactory timeoutFactory() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(TIMEOUT_MS);
        factory.setReadTimeout(TIMEOUT_MS);
        return factory;
    }

    // Circuit Breaker 설정값
    private static final int FAIL_THRESHOLD = 3;           // 몇 번 실패하면 OPEN으로 전환
    private static final int OPEN_DURATION_SECONDS = 30;   // OPEN 유지 시간 (초)

    /**
     * 5초마다 실행.
     * fixedDelay: 이전 실행 완료 후 5초 뒤에 다시 실행 (누적 방지)
     */
    @Scheduled(fixedDelay = 5000)
    public void checkAllWorkers() {
        List<WorkerNode> workers = workerNodeRepository.findAll();

        for (WorkerNode worker : workers) {
            try {
                processWorker(worker);
            } catch (Exception e) {
                // 스케줄러 자체가 죽지 않도록 개별 워커 에러를 잡아서 로깅
                log.error("[HealthCheck] {} 처리 중 예외 발생: {}", worker.getName(), e.getMessage());
            }
        }
    }

    private void processWorker(WorkerNode worker) {
        CircuitState state = worker.getCircuitState();

        // ── OPEN 상태: 30초가 지났으면 HALF_OPEN으로 전환 ──────────
        if (state == CircuitState.OPEN) {
            long elapsed = java.time.Duration.between(worker.getOpenAt(), LocalDateTime.now()).getSeconds();
            if (elapsed >= OPEN_DURATION_SECONDS) {
                worker.setCircuitState(CircuitState.HALF_OPEN);
                log.info("[Circuit] {} OPEN → HALF_OPEN ({}초 경과)", worker.getName(), elapsed);
            } else {
                // 아직 30초가 안 지났으면 헬스체크 스킵
                return;
            }
        }

        // ── CLOSED / HALF_OPEN: 실제 헬스체크 요청 ─────────────────
        long startTime = System.currentTimeMillis();
        boolean isHealthy = sendHealthCheck(worker.getUrl());
        long responseTime = System.currentTimeMillis() - startTime;

        worker.setLastCheckedAt(LocalDateTime.now());
        worker.setResponseTimeMs(responseTime);

        if (isHealthy) {
            onSuccess(worker);
        } else {
            onFailure(worker);
        }

        workerNodeRepository.save(worker);
    }

    /** 헬스체크 성공 시: 카운터 초기화, 상태 HEALTHY, 서킷 CLOSED */
    private void onSuccess(WorkerNode worker) {
        if (worker.getCircuitState() == CircuitState.HALF_OPEN) {
            log.info("[Circuit] {} HALF_OPEN → CLOSED (복구 완료)", worker.getName());
        }
        worker.setStatus(WorkerStatus.HEALTHY);
        worker.setCircuitState(CircuitState.CLOSED);
        worker.setFailCount(0);
    }

    /** 헬스체크 실패 시: 카운터 증가, FAIL_THRESHOLD 초과 시 OPEN */
    private void onFailure(WorkerNode worker) {
        int newFailCount = worker.getFailCount() + 1;
        worker.setFailCount(newFailCount);
        worker.setStatus(WorkerStatus.UNHEALTHY);

        if (newFailCount >= FAIL_THRESHOLD) {
            worker.setCircuitState(CircuitState.OPEN);
            worker.setOpenAt(LocalDateTime.now());
            log.warn("[Circuit] {} CLOSED → OPEN ({}회 연속 실패)", worker.getName(), newFailCount);
        } else {
            log.warn("[HealthCheck] {} 실패 ({}/{}회)", worker.getName(), newFailCount, FAIL_THRESHOLD);
        }
    }

    /**
     * 워커 PC의 /health 엔드포인트 호출.
     * 타임아웃 3초 - 응답 없으면 false 반환
     */
    private boolean sendHealthCheck(String baseUrl) {
        try {
            String response = restClient.get()
                    .uri(baseUrl + "/health")
                    .retrieve()
                    .body(String.class);
            return response != null;
        } catch (Exception e) {
            return false;
        }
    }
}
