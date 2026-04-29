FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치 (OpenCV 등 이미지 처리 라이브러리가 필요할 경우 대비)
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
RUN apt-get update && apt-get install -y curl libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 소스 코드 복사
COPY . .

# AI 서버 포트 개방
EXPOSE 8000

# GW 모듈의 독립 서버 실행 (CLI 실행 방식 준수)
CMD ["python", "-m", "GW.dev_server"]
