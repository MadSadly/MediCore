package com.example.backend_main.worker;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface WorkerNodeRepository extends JpaRepository<WorkerNode, Long> {

    Optional<WorkerNode> findByName(String name);

    // OPEN 상태인 워커 목록 조회 (복구 타이머 체크용)
    List<WorkerNode> findByCircuitState(CircuitState circuitState);
}
