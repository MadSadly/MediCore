FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends     curl     libgl1     libglib2.0-0     && rm -rf /var/lib/apt/lists/*

# Build context: AI/ 디렉토리에서 실행
# docker build -f NJ/Dockerfile .
COPY requirements.txt .
COPY NJ/requirements.txt ./NJ_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r NJ_requirements.txt

COPY NJ/ ./NJ/

EXPOSE 8000

CMD ["python", "-m", "NJ.dev_server"]
