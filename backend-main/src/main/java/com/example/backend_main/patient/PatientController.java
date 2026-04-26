package com.example.backend_main.patient;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api/patients")
@RequiredArgsConstructor
public class PatientController {

    private final PatientRepository patientRepository;

    @GetMapping
    public List<Patient> list() {
        return patientRepository.findAll();
    }

    @GetMapping("/{id}")
    public Patient get(@PathVariable String id) {
        return patientRepository.findByUid(id)
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "환자를 찾을 수 없습니다."));
    }

    @PostMapping
    public ResponseEntity<Patient> create(@RequestBody Patient patient) {
        return ResponseEntity.status(HttpStatus.CREATED).body(patientRepository.save(patient));
    }
}