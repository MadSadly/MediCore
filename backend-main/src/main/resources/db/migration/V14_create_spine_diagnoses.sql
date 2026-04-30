-- auto-generated definition
create table spine_diagnosis_history
(
    diagnosis_id      bigserial
        primary key,
    patient_id        varchar(50),
    mri_image_path    varchar(255) not null,
    clinical_symptoms jsonb        not null,
    dl_vision_result  jsonb        not null,
    llm_medical_note  text         not null,
    llm_final_report  text         not null,
    created_at        timestamp default CURRENT_TIMESTAMP
);

alter table spine_diagnosis_history
    owner to medicore;

CREATE TABLE spine_diagnosis (
                                 id BIGSERIAL PRIMARY KEY,
                                 patient_id VARCHAR(50),
                                 image_url VARCHAR(255) NOT NULL,

    -- AI 분석 데이터 (JSON 형태로 저장하여 유연성 확보)
                                 vision_analysis_json TEXT NOT NULL,
                                 clinical_data_json TEXT NOT NULL,

    -- LLM 생성 리포트
                                 medical_note TEXT,
                                 final_report TEXT,

                                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

