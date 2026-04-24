-- ================================================================
-- Worker PC 상태 추적 테이블
-- Spring Boot 스케줄러가 5초마다 이 테이블을 업데이트함
-- ================================================================

CREATE TABLE worker_nodes (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(50)  NOT NULL UNIQUE, -- 'skin', 'brain', 'eyes' 등
    display_name    VARCHAR(100) NOT NULL,         -- '피부 진단 서버' 등 화면 표시용
    url             VARCHAR(255) NOT NULL,         -- 'http://192.168.0.101:8000'
    status          VARCHAR(20)  NOT NULL DEFAULT 'UNKNOWN',
                    -- HEALTHY: 정상 | UNHEALTHY: 장애 | UNKNOWN: 미확인
    circuit_state   VARCHAR(20)  NOT NULL DEFAULT 'CLOSED',
                    -- CLOSED: 정상 통신 | OPEN: 차단(장애) | HALF_OPEN: 복구 시도 중
    fail_count      INT          NOT NULL DEFAULT 0,  -- 연속 실패 횟수
    open_at         TIMESTAMP,                         -- OPEN 상태로 전환된 시각
    last_checked_at TIMESTAMP,                         -- 마지막 헬스체크 시각
    response_time_ms BIGINT,                           -- 응답 시간 (ms)
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

INSERT INTO worker_nodes (name, display_name, url) VALUES
    ('skin',   '피부 진단 서버',   'http://192.168.0.20:8000'),
    ('brain',  '뇌종양 진단 서버', 'http://192.168.0.9:8000'),
    ('eyes',   '안과 진단 서버',   'http://192.168.0.32:8000'),
    ('spine',  '척추 진단 서버',   'http://192.168.0.13:8000'),
    ('kidney', '신장 진단 서버',   'http://192.168.0.5:8000'),
    ('colon',  '대장암 진단 서버', 'http://192.168.0.73:8000');