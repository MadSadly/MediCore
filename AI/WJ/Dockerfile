FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY WJ/requirements_wj.txt .
RUN pip install --no-cache-dir -r requirements_wj.txt

# HD-BET 모델 weights 다운로드 (빌드 시 1회, ~200MB)
RUN python -c "from HD_BET.checkpoint_download import maybe_download_parameters; maybe_download_parameters()"

COPY . .

EXPOSE 8000

CMD ["python", "-m", "WJ.dev_server"]
