import streamlit as st
import pandas as pd
import joblib
import requests
import google.generativeai as genai

# Gemini API 및 Spring Boot API 설정
genai.configure(api_key="AIzaSyCry1oySeOFzgpbyeRedS1GGccKm6hR0Po")
SPRING_BOOT_API_URL = "http://localhost:8080/api/consultations/save"

class ConsultationService:
    def __init__(self, model_path='AI/GW/colorectal_cancer_model.pkl'):
        self.model = joblib.load(model_path)
        self.llm_model = genai.GenerativeModel('gemini-2.5-flash')

    def predict(self, patient_data):
        df = pd.DataFrame([patient_data])
        prediction = self.model.predict(df)[0]
        probability = self.model.predict_proba(df)[0][1]
        return "Yes" if prediction == 1 else "No", float(probability)

    def retrieve_vector_knowledge(self, stage, treatment):
        # 실제 환경에서는 ChromaDB/FAISS 등을 활용한 쿼리 로직이 구현될 영역입니다.
        mock_vdb = {
            "Localized": "국소성 대장암은 1~2기로 분류되며 외과적 절제술 예후가 좋습니다.",
            "Combination": "복합 치료(병용 요법)는 재발 방지와 종양 축소에 높은 효과를 보입니다."
        }
        return f"- {mock_vdb.get(stage, '해당 단계에 대한 일반 지식.')}\n- {mock_vdb.get(treatment, '해당 치료의 일반 지식.')}"

    def generate_llm_response(self, data, pred, prob, context):
        prompt = f"""
        대장암 전문 AI 상담 봇으로서 아래 정보를 바탕으로 환자에게 희망적이고 전문적인 답변을 한국어로 작성하세요.
        [환자 상태] 나이:{data['Age']}, 성별:{data['Gender']}, 병기:{data['Cancer_Stage']}, 치료:{data['Treatment_Type']}
        [AI 생존 예측] {pred} (확률: {prob:.1%})
        [의학 지식(RAG)] {context}
        """
        response = self.llm_model.generate_content(prompt)
        return response.text

    def save_to_db(self, db_payload):
        try:
            response = requests.post(SPRING_BOOT_API_URL, json=db_payload)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Spring Boot 연동 실패: {e}")
            return False

def main():
    st.set_page_config(page_title="대장암 AI 상담", layout="wide")
    st.title("🩺 대장암 AI 상담 프로그램")

    service = ConsultationService()

    with st.form("consultation_form"):
        st.subheader("환자 정보 입력")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("나이", value=65)
            gender = st.selectbox("성별", ["M", "F"])
            cancer_stage = st.selectbox("암 단계", ["Localized", "Regional", "Distant"])
        with col2:
            tumor_size = st.number_input("종양 크기 (mm)", min_value=1, max_value=150, value=30)
            treatment = st.selectbox("치료 방법", ["Chemotherapy", "Combination", "Surgery"])

        submit = st.form_submit_button("결과 예측 및 상담 받기")

    if submit:
        # 모델 예측을 위한 필수 컬럼 (나머지는 더미값 처리)
        patient_data = {
            'Age': age, 'Gender': gender, 'Cancer_Stage': cancer_stage, 'Tumor_Size_mm': tumor_size,
            'Treatment_Type': treatment, 'Country': 'UK', 'Family_History': 'No', 'Smoking_History': 'No',
            'Alcohol_Consumption': 'No', 'Obesity_BMI': 'Normal', 'Diet_Risk': 'Low', 'Physical_Activity': 'Moderate',
            'Diabetes': 'No', 'Inflammatory_Bowel_Disease': 'No', 'Genetic_Mutation': 'No', 'Screening_History': 'Regular',
            'Early_Detection': 'Yes', 'Survival_5_years': 'Yes', 'Mortality': 'No', 'Healthcare_Costs': 50000, 'Incidence_Rate_per_100K': 50,
            'Mortality_Rate_per_100K': 20, 'Urban_or_Rural': 'Urban', 'Economic_Classification': 'Developed',
            'Healthcare_Access': 'High', 'Insurance_Status': 'Insured'
        }

        with st.spinner("분석 및 상담 내용을 생성 중입니다..."):
            # 1. 예측
            pred, prob = service.predict(patient_data)

            # 2. Vector DB 지식 검색
            context = service.retrieve_vector_knowledge(cancer_stage, treatment)

            # 3. LLM 상담 생성
            llm_reply = service.generate_llm_response(patient_data, pred, prob, context)

            # 화면 출력
            st.success("상담 완료")
            st.markdown(f"**생존 예측 결과:** {pred} (확률: {prob:.1%})")
            st.info(llm_reply)

            # 4. Spring Boot 테이블 저장
            db_payload = {
                "age": age, "gender": gender, "cancerStage": cancer_stage,
                "tumorSizeMm": tumor_size, "treatmentType": treatment,
                "predictedSurvival": pred, "survivalProbability": prob,
                "llmConsultationSummary": llm_reply
            }
            if service.save_to_db(db_payload):
                st.toast("✅ 상담 결과가 안전하게 서버에 저장되었습니다.")

if __name__ == "__main__":
    main()
