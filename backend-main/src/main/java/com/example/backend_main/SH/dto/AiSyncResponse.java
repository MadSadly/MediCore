package com.example.backend_main.SH.dto;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.NoArgsConstructor;

import static com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.ANY;
import static com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility.NONE;

@JsonIgnoreProperties(ignoreUnknown = true)
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
@JsonAutoDetect(getterVisibility = NONE, isGetterVisibility = NONE, setterVisibility = NONE, fieldVisibility = ANY)
@Getter
@NoArgsConstructor
public class AiSyncResponse {

    private String sessionId;
    private AiDlResult dlResult;
    private AiEmergency emergency;
    private String report;
    private Double inferenceTimeMs;
    private Double qualityScore;
    private String timestamp;

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    @JsonAutoDetect(getterVisibility = NONE, isGetterVisibility = NONE, setterVisibility = NONE, fieldVisibility = ANY)
    @Getter
    @NoArgsConstructor
    public static class AiDlResult {

        private AiPrimaryDisease primaryDisease;
        private AiStage stage;
        private String gradcamBase64;
        private String modelVersion;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    @JsonAutoDetect(getterVisibility = NONE, isGetterVisibility = NONE, setterVisibility = NONE, fieldVisibility = ANY)
    @Getter
    @NoArgsConstructor
    public static class AiPrimaryDisease {

        private String diseaseName;
        private Double confidence;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    @JsonAutoDetect(getterVisibility = NONE, isGetterVisibility = NONE, setterVisibility = NONE, fieldVisibility = ANY)
    @Getter
    @NoArgsConstructor
    public static class AiStage {

        private Integer stage;
        private String stageName;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    @JsonAutoDetect(getterVisibility = NONE, isGetterVisibility = NONE, setterVisibility = NONE, fieldVisibility = ANY)
    @Getter
    @NoArgsConstructor
    public static class AiEmergency {

        private Boolean isEmergency;
        private String reason;
    }
}
