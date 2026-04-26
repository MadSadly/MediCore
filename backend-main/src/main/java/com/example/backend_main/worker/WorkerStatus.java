package com.example.backend_main.worker;

public enum WorkerStatus {
    HEALTHY,    // 정상
    UNHEALTHY,  // 장애
    UNKNOWN     // 아직 체크 안 됨
}