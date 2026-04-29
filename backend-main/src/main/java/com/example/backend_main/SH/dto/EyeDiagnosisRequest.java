package com.example.backend_main.SH.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class EyeDiagnosisRequest {

    private String patientId;
    private Integer patientAge;
    private Boolean hasDiabetes;
    private Boolean hasHypertension;
    private String clinicalNote;
}
