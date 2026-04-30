package com.example.backend_main.GW;

import com.example.backend_main.GW.ColonService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/gw/colon")
@RequiredArgsConstructor
public class ColonController {
    private final ColonService colonService;

    @PostMapping("/predict/{patientUid}")
    public ResponseEntity<?> diagnose(@PathVariable String patientUid, @RequestBody Map<String, Object> inputs) {
        try {
            return ResponseEntity.ok(colonService.predictAndSave(patientUid, inputs));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(e.getMessage());
        }
    }

    @GetMapping("/history/{patientUid}")
    public ResponseEntity<?> getHistory(@PathVariable String patientUid) {
        return ResponseEntity.ok(colonService.getHistory(patientUid));
    }
}