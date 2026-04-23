package com.example.backend_main.worker;

public enum CircuitState {
    CLOSED,     // 정상: 요청 통과
    OPEN,       // 차단: 연속 3회 실패 → 30초간 요청 막음
    HALF_OPEN   // 복구 시도: OPEN 30초 후 → 1번 테스트 요청
}
