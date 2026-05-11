import os
import logging
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

class ColonRAGEngine:
    def __init__(self):
        self.model = GenerativeModel("gemini-1.5-flash")

    async def get_advice(self, query: str, module: str = "colon"):
        # 가이드라인 준수: module='colon' 필터링 (여기서는 프롬프트에 컨텍스트로 주입)
        prompt = f"""
        너는 대장암 전문 AI 컨설턴트야. 아래의 환자 데이터를 바탕으로 전문적인 소견과 관리 가이드를 작성해줘.
        담당 모듈: {module}
        
        환자 상황:
        {query}
        
        작성 가이드라인:
        1. 발병 위험 예측 결과에 따른 임상적 의미 설명.
        2. 종양 크기 및 암 단계에 따른 권장 관리 방안.
        3. 식단(Diet Risk) 및 생활 습관 개선 제안.
        4. 마지막에는 "본 결과는 AI 보조 진단이며 최종 판단은 의사가 내려야 합니다."라는 문구를 반드시 포함할 것.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return "현재 상담 엔진을 사용할 수 없습니다. 일반적인 대장암 관리 수칙을 참고하세요."
