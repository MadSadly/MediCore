package com.example.backend_main.NJ.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
public class KidneyDiagnosisRequest {

    // 진단 결과
    private String result;
    private double confidence;
    private String description;
    private String severity;
    private boolean dialysisRequired;
    private Map<String, Double> probabilities;

    // 임상 수치
    private Double egfr;
    private Double sc;
    private Double bu;
    private Double pot;
    private Double al;
    private Double bp;
    private Double bgr;
    private Double hemo;

    // 동반 증상
    private String htn;
    private String dm;
    private String pe;
}
