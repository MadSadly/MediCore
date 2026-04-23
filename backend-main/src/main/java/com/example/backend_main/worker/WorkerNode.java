package com.example.backend_main.worker;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;

@Entity
@Table(name = "worker_nodes")
@Getter @Setter
public class WorkerNode {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;           // 'skin', 'brain' 등 고유 식별자

    @Column(nullable = false)
    private String displayName;    // '피부 진단 서버' 화면 표시용

    @Column(nullable = false)
    private String url;            // 'http://192.168.0.101:8000'

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private WorkerStatus status = WorkerStatus.UNKNOWN;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CircuitState circuitState = CircuitState.CLOSED;

    @Column(nullable = false)
    private int failCount = 0;     // 연속 실패 횟수 (3회 초과 시 OPEN)

    private LocalDateTime openAt;           // OPEN 전환 시각
    private LocalDateTime lastCheckedAt;    // 마지막 헬스체크 시각
    private Long responseTimeMs;            // 응답 시간 (ms)
}
