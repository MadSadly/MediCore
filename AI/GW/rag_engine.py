import psycopg2

class ColonRAGEngine:
    async def get_advice(self, query: str, module: str = "colon"):
        # 반드시 module = 'colon' 필터가 포함되어야 합니다.
        sql = """
            SELECT content FROM medical_knowledge 
            WHERE module = %s 
            ORDER BY embedding <=> %s 
            LIMIT 3
        """
        # (임베딩 및 DB 연결 로직 생략...)
        return "조회된 데이터를 기반으로 생성된 대장암 예방 및 관리 가이드입니다."
