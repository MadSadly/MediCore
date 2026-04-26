package com.example.backend_main.worker;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/workers")
@RequiredArgsConstructor
public class WorkerNodeController {

    private final WorkerNodeRepository workerNodeRepository;

    /** 전체 워커 상태 조회 - 프론트 대시보드에서 사용 */
    @GetMapping
    public ResponseEntity<List<WorkerNode>> getAllWorkers() {
        return ResponseEntity.ok(workerNodeRepository.findAll());
    }

    /** 특정 워커 상태 조회 */
    @GetMapping("/{name}")
    public ResponseEntity<WorkerNode> getWorker(@PathVariable String name) {
        return workerNodeRepository.findByName(name)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /** 워커 URL 업데이트 (IP 변경 시 사용) */
    @PatchMapping("/{name}/url")
    public ResponseEntity<WorkerNode> updateUrl(
            @PathVariable String name,
            @RequestParam String url) {
        return workerNodeRepository.findByName(name)
                .map(worker -> {
                    worker.setUrl(url);
                    return ResponseEntity.ok(workerNodeRepository.save(worker));
                })
                .orElse(ResponseEntity.notFound().build());
    }
}