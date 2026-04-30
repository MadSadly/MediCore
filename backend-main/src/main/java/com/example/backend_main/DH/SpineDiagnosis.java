import jakarta.persistence.*; // (또는 javax.persistence.*)
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "spine_diagnosis_history") // ⭐️ 딱 이 한 줄만 추가되었습니다!
@Getter @Setter @NoArgsConstructor
public class SpineDiagnosis {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String imageUrl;
    private String visionAnalysisJson; // DL 결과
    private String clinicalDataJson;   // 문진표 결과
    private String medicalNote;        // LLM 소견
    private String final_report;       // 환자용 리포트
}