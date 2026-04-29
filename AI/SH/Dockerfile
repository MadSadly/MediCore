# 시연 배포용 (개발규칙.md / serverGuide.md)
# 빌드: cd MediCore/AI  →  docker build -f SH/Dockerfile -t medicore-sh .
# 실행: docker run -p 8000:8000 --env-file ../.env medicore-sh

FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY SH/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY SH/ /app/SH/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "-m", "SH.dev_server"]
