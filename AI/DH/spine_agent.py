import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGeminiAI

# 1. 상태(State) 정의: 문진표 데이터(clinical_data) 추가
class AgentState(TypedDict):
    raw_data: dict         # 비전 AI 모델이 준 JSON (MRI 판독 수치)
    clinical_data: dict    # [NEW] 의사가 체크한 환자 문진표 데이터
    analysis: str          # 수치 분석 결과
    medical_note: str      # 의학적 소견
    final_report: str      # 환자용 최종 리포트

llm = ChatGeminiAI(model="gemini-2.0-flash")

# 3. 노드 함수들 정의 (프롬프트 변경)
def analyze_data(state: AgentState):
    mri_data = state['raw_data']
    clinical_symptoms = state['clinical_data']

    # [NEW] MRI 수치와 문진표를 결합하여 분석하도록 프롬프트 고도화
    prompt = f"""
    당신은 척추 질환 전문 AI입니다. 다음 두 가지 데이터를 종합하여 환자의 상태를 분석해 주세요.

    [1. 비전 AI의 MRI 판독 수치 (질환별 중증도 확률)]: 
    {mri_data}

    [2. 의사 문진 데이터 (임상 증상)]:
    {clinical_symptoms}

    작업 지시:
    1. MRI 판독 결과 중 가장 심각한 부위와 중증도를 파악하세요.
    2. 해당 영상의학적 결과가 환자의 실제 임상 증상(특히 Red Flag 유무나 통증 기간)과 어떻게 연관되는지 설명하세요.
    3. 수술적 치료가 필요한지, 보존적 치료가 필요한지 1차적인 방향성을 제시하세요.
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