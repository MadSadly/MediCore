FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# MS 전용 의존성 설치
COPY MS/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# AI 전체 소스 복사 (MS 모듈이 루트 기준으로 import)
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/ai/skin/health || exit 1

CMD ["python", "-m", "MS.dev_server"]
