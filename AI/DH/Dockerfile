FROM python:3.10-slim

WORKDIR /app

# 시스템 라이브러리 설치 (팀 공통: 비전 처리 및 헬스체크용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 패키지 설치 (프로젝트 루트의 requirements를 쓰는지, DH 전용을 쓰는지에 따라)
# 팀 공통 requirements.txt를 사용한다고 가정
COPY DH/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# AI 전체 소스 복사 (다른 모듈과의 의존성 문제 방지)
COPY . .

EXPOSE 8000

# 팀 실행 컨벤션에 완벽하게 맞춤 (모듈 실행 방식)
CMD ["python", "-m", "DH.dev_server"]