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
    private String ragAnswer;

    // 수치형 임상 지표 (전체)
    private Double egfr;
    private Double sc;
    private Double bu;
    private Double pot;
    private Double al;
    private Double bp;
    private Double bgr;
    private Double hemo;
    private Double sod;
    private Double pcv;
    private Double wc;
    private Double rc;
    private Double sg;
    private Double su;

    // 환자 기본 정보
    private Double age;
    private String sex;

    // 범주형 임상 지표
    private String rbc;
    private String pc;
    private String pcc;
    private String ba;
    private String cad;
    private String appet;
    private String ane;

    // 동반 증상
    private String htn;
    private String dm;
    private String pe;
}
