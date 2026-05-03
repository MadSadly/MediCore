package com.example.backend_main.DH;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AiResponseDto {
    // DL 모델의 JSON 결과를 유연하게 받기 위해 JsonNode 사용
    @JsonProperty("vision_analysis")
    private JsonNode visionAnalysis;

    @JsonProperty("medical_note")
    private String medicalNote;

    @JsonProperty("final_report")
    private String finalReport;
}