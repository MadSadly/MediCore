import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. 상태(State) 정의: 문진표 데이터(clinical_data) 추가
class AgentState(TypedDict):
    raw_data: dict         # 비전 AI 모델이 준 JSON (MRI 판독 수치)
    clinical_data: dict    # [NEW] 의사가 체크한 환자 문진표 데이터
    analysis: str          # 수치 분석 결과
    medical_note: str      # 의학적 소견
    final_report: str      # 환자용 최종 리포트

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# 3. 노드 함수들 정의 (프롬프트 변경)
def analyze_data(state: AgentState):
    mri_data = state['raw_data']
    clinical_symptoms = state['clinical_data']

    prompt = f"""
    당신은 척추 질환 전문 AI 'Analyzer'입니다. 
    다음 두 가지 데이터를 종합하여 환자의 상태를 분석하고, 다음 단계의 '전문의 AI'가 참고할 수 있도록 구조화된 분석 리포트를 작성해 주세요.

    [1. 비전 AI의 MRI 판독 수치 (질환별 중증도 확률)]: 
    {mri_data}

    [2. 의사 문진 데이터 (임상 증상 및 치료 이력)]:
    {clinical_symptoms}

    작업 지시:
    1. [영상 소견]: MRI 판독 결과 중 'Moderate' 또는 'Severe'에 해당하는 가장 심각한 부위를 특정하세요.
    2. [상호 연관성]: 영상의학적 결과(1번)가 환자의 실제 임상 증상과 논리적으로 일치하는지 분석하세요. 만약 영상은 심각한데 증상이 없거나, 그 반대의 '불일치' 상황이라면 이를 반드시 지적하세요.
    3. [위험도 평가]: 문진 데이터에 'Red Flag(대소변 장애, 진행성 마비 등)'가 포함되어 있다면 최우선 경고사항으로 강조하세요.
    4. [치료 방향성]: 수술적 치료가 필요한지, 보존적 치료가 필요한지 1차적인 방향성을 근거와 함께 제시하세요.

    출력 형식:
    반드시 아래의 마크다운 헤더를 사용하여 명확하게 구분해 주세요.
    - **Primary Finding (주요 영상 소견)**:
    - **Clinical Correlation (임상-영상 연관성)**:
    - **Risk Assessment (위험도 평가)**:
    - **Treatment Direction (치료 방향성)**:
    """
    response = llm.invoke(prompt)
    return {"analysis": response.content}

def write_medical_note(state: AgentState):
    analysis = state['analysis']
    prompt = f"다음 통합 분석 결과를 바탕으로, 전문의가 RAG 가이드라인에 맞춰 참고할 만한 전문적인 의학적 소견서를 작성해줘: {analysis}"
    response = llm.invoke(prompt)
    return {"medical_note": response.content}

def write_final_report(state: AgentState):
    note = state['medical_note']
    prompt = f"다음 전문의 소견을 바탕으로, 환자가 이해하기 쉬운 친절한 최종 리포트를 작성해줘. 향후 치료 방향과 일상생활 주의사항을 명확히 포함해줘: {note}"
    response = llm.invoke(prompt)
    return {"final_report": response.content}

# 4. 그래프 조립
workflow = StateGraph(AgentState)
workflow.add_node("analyzer", analyze_data)
workflow.add_node("expert", write_medical_note)
workflow.add_node("communicator", write_final_report)

workflow.set_entry_point("analyzer")
workflow.add_edge("analyzer", "expert")
workflow.add_edge("expert", "communicator")
workflow.add_edge("communicator", END)

app = workflow.compile()

# 5. 실행 테스트
if __name__ == "__main__":
    # 백엔드에서 넘겨받을 가상의 데이터 구조
    test_mri_data = {
        "Spinal Canal Stenosis": {"Normal_Mild": 0.03, "Moderate": 0.44, "Severe": 0.12},
        "Neural Foraminal Narrowing": {"Normal_Mild": 0.03, "Moderate": 0.02, "Severe": 0.03},
    }

    # [NEW] 프론트엔드에서 전송된 JSON 문진 데이터 예시
    test_clinical_data = {
        "redFlag": [],
        "symptoms": ["하지 방사통", "간헐적 파행"],
        "treatmentHistory": "6주 이상 실패"
    }

    inputs = {
        "raw_data": test_mri_data,
        "clinical_data": test_clinical_data
    }

    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"\n=== Node: {key} ===")
            print(value)