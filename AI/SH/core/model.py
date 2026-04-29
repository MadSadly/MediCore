"""
AI/SH/core/model.py
안과 CDSS — ONNX 추론 엔진
철칙 17: Temperature Scaling (확률 보정)
철칙 18: TTA Horizontal Flip (환경별 ON/OFF)

담당: 홍승현 (SH)
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict

import cv2
import onnxruntime as ort

from ..schemas.response import (
    DiseaseClass, DISEASE_NAMES, STAGE_NAMES,
    DiseaseScore, StageResult, DLResult, EmergencyAlert,
)
from .quality_check import check_post_inference_quality


# ── 커스텀 예외 ───────────────────────────────────────────────
class OODInferenceError(Exception):
    """추론 후 비안과 이미지 판정 시 발생"""
    pass


class ModelLoadError(Exception):
    """ONNX 모델 로드 실패 시 발생"""
    pass


# ── 경로 설정 ─────────────────────────────────────────────────
WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "weights"

ONNX_PATH       = WEIGHTS_DIR / "swin_base_final.onnx"
THRESHOLD_PATH  = WEIGHTS_DIR / "threshold_config.json"
TEMPERATURE_PATH = WEIGHTS_DIR / "temperature.json"

# ── 전처리 파라미터 (Notebook 1과 동일) ──────────────────────
IMG_SIZE = 224  # Swin_Base 입력 크기 (forward에서 512→224 동적 리사이징)
IMG_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
IMG_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)

# ── TTA 환경변수 ──────────────────────────────────────────────
TTA_ENABLED = os.getenv("TTA_ENABLED", "false").lower() == "true"

# ── 응급 판정 기준 (OPH-08) ──────────────────────────────────
EMERGENCY_STAGE_THRESHOLD      = 3     # Stage 3 이상
EMERGENCY_CONFIDENCE_THRESHOLD = 0.88  # 신뢰도 88% 이상
EMERGENCY_COMBO_STAGE          = 2     # 복합 조건 Stage
ELDERLY_AGE_THRESHOLD          = 65    # 고령 기준


class EyeModel:
    """
    Swin_Base ONNX 추론 엔진
    - Temperature Scaling으로 확률 보정 (철칙 17)
    - TTA Horizontal Flip 환경별 ON/OFF (철칙 18)
    - Youden's J 기반 클래스별 임계값 적용
    """

    def __init__(self):
        self._session    = None
        self._temperature = 1.0
        self._thresholds  = {}
        self._loaded      = False

    def load(self):
        """모델 + 설정 파일 로드 (최초 1회)"""
        if self._loaded:
            return

        # ONNX 세션 초기화
        if not ONNX_PATH.exists():
            raise FileNotFoundError(
                f"ONNX 모델 없음: {ONNX_PATH}\n"
                "Notebook 4 완료 후 weights/ 폴더에 배치하세요."
            )

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self._session = ort.InferenceSession(str(ONNX_PATH), providers=providers)

        # Temperature Scaling 로드 (철칙 17)
        if TEMPERATURE_PATH.exists():
            with open(TEMPERATURE_PATH) as f:
                self._temperature = json.load(f).get("T", 1.0)
        else:
            print("⚠️ temperature.json 없음 → T=1.0 (보정 없음)")

        # 임계값 로드 (Youden's J)
        if THRESHOLD_PATH.exists():
            with open(THRESHOLD_PATH) as f:
                self._thresholds = json.load(f)
        else:
            # 기본 임계값 0.5
            self._thresholds = {str(i): 0.5 for i in range(5)}
            print("⚠️ threshold_config.json 없음 → 기본값 0.5 사용")

        self._loaded = True
        provider_name = self._session.get_providers()[0]
        print(f"✅ EyeModel 로드 완료")
        print(f"   Provider: {provider_name}")
        print(f"   Temperature T={self._temperature:.4f}")
        print(f"   TTA: {'ON' if TTA_ENABLED else 'OFF'}")

    def preprocess(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        BGR 이미지 → ONNX 입력 텐서 (1, 3, 512, 512)
        - RGB 변환
        - 512×512 Zero-padding Resize
        - Normalize (ImageNet)
        """
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Zero-padding Resize (원본 비율 보존)
        h, w = img.shape[:2]
        target = 512
        scale  = target / max(h, w)
        nh, nw = int(h * scale), int(w * scale)
        img    = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        ph, pw = target - nh, target - nw
        img    = cv2.copyMakeBorder(
            img, ph // 2, ph - ph // 2,
            pw // 2, pw - pw // 2,
            cv2.BORDER_CONSTANT, value=0,
        )

        # HWC → CHW + Normalize
        img = img.transpose(2, 0, 1).astype(np.float32) / 255.0
        img = (img - IMG_MEAN) / IMG_STD
        return img[np.newaxis]  # (1, 3, 512, 512)

    def _run_inference(self, tensor: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """ONNX 추론 실행 → (disease_logits, stage_logits)"""
        input_name = self._session.get_inputs()[0].name
        outputs    = self._session.run(None, {input_name: tensor})
        return outputs[0], outputs[1]  # (1,5), (1,3,5)

    def _apply_temperature(self, logits: np.ndarray) -> np.ndarray:
        """Temperature Scaling (철칙 17): logits / T → sigmoid"""
        scaled = logits / self._temperature
        return 1.0 / (1.0 + np.exp(-scaled))  # sigmoid

    def _apply_tta(self, tensor: np.ndarray) -> np.ndarray:
        """
        TTA Horizontal Flip (철칙 18)
        원본 + 좌우반전 평균
        Vertical Flip은 절대 사용하지 않음
        """
        flipped = tensor[:, :, :, ::-1].copy()
        orig_logits, orig_stage = self._run_inference(tensor)
        flip_logits, flip_stage = self._run_inference(flipped)

        avg_logits = (orig_logits + flip_logits) / 2.0
        avg_stage  = (orig_stage  + flip_stage)  / 2.0
        return avg_logits, avg_stage

    def predict(
        self,
        img_bgr: np.ndarray,
        patient_age:      int  = None,
        has_diabetes:     bool = False,
        has_hypertension: bool = False,
    ) -> Tuple[DLResult, EmergencyAlert, float]:
        """
        메인 추론 함수

        Returns:
            (DLResult, EmergencyAlert, inference_time_ms)
        """
        if not self._loaded:
            self.load()

        t0     = time.time()
        tensor = self.preprocess(img_bgr)

        # 추론 (TTA 환경별 ON/OFF)
        if TTA_ENABLED:
            disease_logits, stage_logits = self._apply_tta(tensor)
        else:
            disease_logits, stage_logits = self._run_inference(tensor)

        # Temperature Scaling 확률 보정
        disease_probs = self._apply_temperature(disease_logits)[0]  # (5,)
        stage_probs   = self._softmax(stage_logits[0])              # (3, 5)

        inference_time_ms = (time.time() - t0) * 1000

        # 추론 후 OOD 차단 (철칙 16 2차 방어선)
        max_conf = float(disease_probs.max())
        is_fundus, ood_reason = check_post_inference_quality(max_conf)
        if not is_fundus:
            raise OODInferenceError(ood_reason)

        # 클래스별 임계값 적용 (Youden's J)
        all_scores = self._build_disease_scores(disease_probs)

        # 1차 진단 (가장 높은 확률 질환)
        primary_idx     = int(np.argmax(disease_probs))
        primary_disease = all_scores[primary_idx]

        # Stage 예측 (글로코마=0, DR=1, 백내장=2)
        stage_result = self._build_stage_result(stage_probs, primary_idx)

        # 응급 판정 (OPH-08)
        emergency = self._check_emergency(
            primary_disease, stage_result,
            patient_age, has_diabetes, has_hypertension,
        )

        dl_result = DLResult(
            primary_disease=primary_disease,
            all_scores=all_scores,
            stage=stage_result,
            gradcam_base64=None,     # gradcam.py에서 별도 생성
            is_emergency=emergency.is_emergency,
            emergency_reason=emergency.reason,
        )

        return dl_result, emergency, inference_time_ms

    def _build_disease_scores(self, probs: np.ndarray) -> List[DiseaseScore]:
        scores = []
        for i, p in enumerate(probs):
            threshold   = self._thresholds.get(str(i), 0.5)
            is_positive = float(p) >= threshold
            scores.append(DiseaseScore(
                disease_id=i,
                disease_name=DISEASE_NAMES[DiseaseClass(i)],
                confidence=round(float(p), 4),
                is_positive=is_positive,
            ))
        return scores

    def _build_stage_result(
        self,
        stage_probs: np.ndarray,
        primary_idx: int,
    ) -> StageResult | None:
        """Stage Head에서 주요 질환의 중증도 추출"""
        DISEASE_TO_STAGE_IDX = {1: 0, 3: 1, 2: 2}  # glaucoma, dr, cataract
        s_idx = DISEASE_TO_STAGE_IDX.get(primary_idx)
        if s_idx is None:
            return None

        stage = int(np.argmax(stage_probs[s_idx]))
        return StageResult(
            stage=stage,
            stage_name=STAGE_NAMES[stage],
            disease_id=primary_idx,
        )

    def _check_emergency(
        self,
        primary: DiseaseScore,
        stage:   StageResult | None,
        age:     int  | None,
        has_dm:  bool,
        has_htn: bool,
    ) -> EmergencyAlert:
        """
        응급 판정 3가지 복합 조건 (OPH-08):
          ① Stage 3 이상
          ② 신뢰도 88% 이상 + Stage 2 이상
          ③ 당뇨망막병증 + 65세 이상 + 당뇨·고혈압 동반
        """
        stage_val = stage.stage if stage else 0

        # 조건 ①
        if stage_val >= EMERGENCY_STAGE_THRESHOLD:
            return EmergencyAlert(
                is_emergency=True,
                reason=f"중증 병변 감지 (Stage {stage_val})",
                emergency_level=3,
            )

        # 조건 ②
        if (primary.confidence >= EMERGENCY_CONFIDENCE_THRESHOLD
                and stage_val >= EMERGENCY_COMBO_STAGE):
            return EmergencyAlert(
                is_emergency=True,
                reason=(
                    f"고확신 중등도 병변 "
                    f"(신뢰도 {primary.confidence:.0%}, Stage {stage_val})"
                ),
                emergency_level=2,
            )

        # 조건 ③
        if (primary.disease_id == DiseaseClass.DR
                and age is not None and age >= ELDERLY_AGE_THRESHOLD
                and has_dm and has_htn):
            return EmergencyAlert(
                is_emergency=True,
                reason="당뇨망막병증 + 고령 + 당뇨·고혈압 복합 위험",
                emergency_level=2,
            )

        return EmergencyAlert(
            is_emergency=False,
            reason=None,
            emergency_level=0,
        )

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        e = np.exp(x - x.max(axis=-1, keepdims=True))
        return e / e.sum(axis=-1, keepdims=True)


# ── 싱글턴 인스턴스 ──────────────────────────────────────────
eye_model = EyeModel()
