package com.example.backend_main.NJ.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
public class KidneyDiagnosisRequest {

    private String result;
    private double confidence;
    private String description;
    private String severity;
    private boolean dialysisRequired;
    private Double egfr;
    private Map<String, Double> probabilities;
}
