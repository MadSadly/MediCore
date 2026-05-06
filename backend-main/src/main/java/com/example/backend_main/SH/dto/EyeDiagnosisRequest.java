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
    private Boolean hasDiabetes = false;
    private Boolean hasHypertension = false;
    private String clinicalNote;
}
