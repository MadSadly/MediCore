"""
AI/SH/core/quality_check.py
안과 CDSS — 이미지 품질 검증 (OPH-05)
철칙 16: Laplacian 필터 최전방 배치 (OOD 차단)

검증 순서 (Fail-Fast):
  1. 파일 크기 (가장 빠름)
  2. 파일 형식
  3. 이미지 디코딩
  4. 해상도 (512px 미만 거부)
  5. 종횡비 (1.5 초과 거부)
  6. 안저 유효 영역 마스킹
  7. Red 채널 우세 검증 (안저 고유 색상, 마스킹 영역만)
  8. 평균 밝기 (과노출/저노출)
  9. Laplacian 블러 감지 (핵심)
 10. 추론 후 OOD 차단 (별도 함수)
"""

import os

import cv2
import numpy as np
from typing import Tuple, Optional

from ..schemas.response import ImageQualityResult, ErrorCode


# ── 임계값 설정 ───────────────────────────────────────────────
# Laplacian 분산: 마스크 안저 영역 기준. 낮을수록 흐림.
# 100은 실촬영·압축 이미지에서 자주 걸려 기본 70 (엄격: .env 에 SH_LAPLACIAN_THRESHOLD=100)
LAPLACIAN_THRESHOLD = float(os.getenv("SH_LAPLACIAN_THRESHOLD", "70.0"))
MIN_RESOLUTION        = 512     # 최소 단변 해상도
MAX_ASPECT_RATIO      = 1.5     # 최대 종횡비 (안저는 거의 1:1)
MAX_FILE_SIZE_MB      = 20      # 최대 파일 크기
MASK_PIXEL_THRESHOLD  = 15      # 검은 배경 제거 임계값
MIN_FOREGROUND_RATIO  = 0.10    # 유효 영역 최소 비율 (10%)
MIN_MEAN_INTENSITY    = 20.0    # 최소 평균 밝기 (저노출 차단)
MAX_MEAN_INTENSITY    = 235.0   # 최대 평균 밝기 (과노출 차단)
POST_CONF_THRESHOLD   = 0.3     # 추론 후 OOD 판정 임계값

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


def check_image_quality(
    image_bytes: bytes,
    filename: str,
) -> Tuple[ImageQualityResult, Optional[np.ndarray]]:
    """
    이미지 품질 검증 메인 함수 (Fail-Fast 순서)

    Returns:
        (ImageQualityResult, np.ndarray | None)
        통과 시 BGR ndarray 반환, 실패 시 None
    """

    # ── Step 1: 파일 크기 ────────────────────────────────────
    file_size_mb = len(image_bytes) / (1024 ** 2)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return _reject(
            ErrorCode.IMAGE_TOO_LARGE,
            f"파일 크기 {file_size_mb:.1f}MB (최대 {MAX_FILE_SIZE_MB}MB)",
        ), None

    # ── Step 2: 파일 형식 ────────────────────────────────────
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext not in SUPPORTED_FORMATS:
        return _reject(
            ErrorCode.INVALID_IMAGE_FORMAT,
            f"지원 형식: JPG, PNG, TIFF (입력: {ext})",
        ), None

    # ── Step 3: 이미지 디코딩 ────────────────────────────────
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return _reject(
            ErrorCode.INVALID_IMAGE_FORMAT,
            "이미지 디코딩 실패",
        ), None

    h, w = img.shape[:2]

    # ── Step 4: 해상도 ───────────────────────────────────────
    if min(h, w) < MIN_RESOLUTION:
        return _reject(
            ErrorCode.IMAGE_QUALITY_TOO_LOW,
            f"해상도 {w}×{h} (최소 {MIN_RESOLUTION}px 이상 필요)",
        ), None

    # ── Step 5: 종횡비 ───────────────────────────────────────
    aspect_ratio = max(h, w) / min(h, w)
    if aspect_ratio > MAX_ASPECT_RATIO:
        return _reject(
            ErrorCode.INVALID_IMAGE_FORMAT,
            f"비정상적인 이미지 비율 {aspect_ratio:.2f} (안저 이미지는 정사각형에 가까워야 함)",
        ), None

    # ── Step 6: 안저 유효 영역 마스킹 (먼저 실행) ───────────
    # 검은 배경(여백)을 제거하고 실제 안구 영역만 분석
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray > MASK_PIXEL_THRESHOLD

    foreground_ratio = mask.sum() / (h * w)
    if foreground_ratio < MIN_FOREGROUND_RATIO:
        return _reject(
            ErrorCode.IMAGE_QUALITY_TOO_LOW,
            f"유효한 안저 영역 부족 (유효 비율: {foreground_ratio:.1%})",
        ), None

    # ── Step 7: Red 채널 우세 검증 (마스킹 영역에서만) ───────
    # 검은 배경을 제외한 실제 안구 영역의 색상 평균으로 판정
    b_mean, g_mean, r_mean = cv2.mean(img, mask=mask.astype(np.uint8))[:3]
    if r_mean <= g_mean or r_mean <= b_mean:
        return _reject(
            ErrorCode.IMAGE_NOT_FUNDUS,
            f"안저 고유의 색상 분포(Red 우세)가 아닙니다 "
            f"(R:{r_mean:.1f} G:{g_mean:.1f} B:{b_mean:.1f})",
        ), None

    # ── Step 8: 평균 밝기 (과노출/저노출) ────────────────────
    mean_intensity = float(gray[mask].mean())
    if mean_intensity < MIN_MEAN_INTENSITY:
        return _reject(
            ErrorCode.IMAGE_QUALITY_TOO_LOW,
            f"이미지 저노출 (평균 밝기: {mean_intensity:.1f}, 최소: {MIN_MEAN_INTENSITY})",
        ), None
    if mean_intensity > MAX_MEAN_INTENSITY:
        return _reject(
            ErrorCode.IMAGE_QUALITY_TOO_LOW,
            f"이미지 과노출 (평균 밝기: {mean_intensity:.1f}, 최대: {MAX_MEAN_INTENSITY})",
        ), None

    # ── Step 9: Laplacian 블러 감지 (핵심 — 철칙 16) ─────────
    # 마스킹된 안구 영역에 대해서만 분산 계산
    laplacian     = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = float(laplacian[mask].var())

    if laplacian_var < LAPLACIAN_THRESHOLD:
        return ImageQualityResult(
            is_valid=False,
            laplacian_var=laplacian_var,
            quality_score=_normalize_quality_score(laplacian_var),
            error_code=ErrorCode.IMAGE_QUALITY_TOO_LOW,
            rejection_reason=(
                f"판독 불가 — 이미지 재촬영 요망 "
                f"(선명도: {laplacian_var:.1f}, 기준: {LAPLACIAN_THRESHOLD})"
            ),
        ), None

    # ── 통과 ─────────────────────────────────────────────────
    return ImageQualityResult(
        is_valid=True,
        laplacian_var=laplacian_var,
        quality_score=_normalize_quality_score(laplacian_var),
        error_code=None,
        rejection_reason=None,
    ), img


def check_post_inference_quality(
    max_confidence: float,
) -> Tuple[bool, Optional[str]]:
    """
    모델 추론 후 비안과 이미지 2차 차단 (철칙 16)
    max_confidence < 0.3 → 비안과 이미지로 판정

    Returns:
        (is_fundus, rejection_reason)
    """
    if max_confidence < POST_CONF_THRESHOLD:
        return False, (
            f"안저 이미지가 아닌 것으로 판단됩니다 "
            f"(최대 확신도: {max_confidence:.2f}, 기준: {POST_CONF_THRESHOLD})"
        )
    return True, None


def _reject(error_code: str, reason: str) -> ImageQualityResult:
    """거부 응답 생성 헬퍼"""
    return ImageQualityResult(
        is_valid=False,
        laplacian_var=0.0,
        quality_score=0.0,
        error_code=error_code,
        rejection_reason=reason,
    )


def _normalize_quality_score(laplacian_var: float) -> float:
    """Laplacian 분산 → 0~1 품질 점수 정규화"""
    if laplacian_var <= 0:
        return 0.0
    return round(min(laplacian_var / 500.0, 1.0), 4)
