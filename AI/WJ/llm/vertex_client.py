from __future__ import annotations

import os
from typing import Optional

_gemini_model = None


def get_gemini_model():
    """Gemini 모델 싱글톤. 첫 호출 시 초기화."""
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model

    import vertexai
    from vertexai.generative_models import GenerativeModel

    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast3")
    key_path = os.getenv("GCP_KEY_PATH")

    if not project:
        raise RuntimeError("GCP_PROJECT_ID 환경변수가 설정되지 않았습니다.")

    if key_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    vertexai.init(project=project, location=location)

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
    _gemini_model = GenerativeModel(model_name)
    return _gemini_model


def generate_text(prompt: str, temperature: float = 0.3, max_tokens: int = 8192) -> str:
    from vertexai.generative_models import GenerationConfig

    model = get_gemini_model()
    config = GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )
    response = model.generate_content(prompt, generation_config=config)
    return response.text
