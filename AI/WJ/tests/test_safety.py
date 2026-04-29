from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from WJ.core.safety import apply_safety_check, DISCLAIMER


def _clf(pred, conf, tumor_prob=None):
    if tumor_prob is None:
        tumor_prob = conf if pred == "Tumor" else 1 - conf
    return {
        "prediction": pred,
        "confidence": conf,
        "tumor_probability": tumor_prob,
        "normal_probability": 1 - tumor_prob,
    }


def test_low_confidence_triggers_high_uncertainty():
    assessment, _ = apply_safety_check(_clf("Tumor", 0.80))
    assert assessment.risk_level == "high_uncertainty"
    assert assessment.requires_specialist_review is True


def test_tumor_moderate_confidence():
    assessment, _ = apply_safety_check(_clf("Tumor", 0.90))
    assert assessment.risk_level == "moderate"
    assert assessment.requires_specialist_review is True


def test_tumor_high_confidence():
    assessment, _ = apply_safety_check(_clf("Tumor", 0.97))
    assert assessment.risk_level == "low"
    assert assessment.requires_specialist_review is False


def test_normal_with_residual_tumor_prob():
    assessment, _ = apply_safety_check(_clf("Normal", 0.92, tumor_prob=0.08))
    assert assessment.risk_level == "low"
    assert "추적 관찰" in assessment.clinical_action


def test_normal_clean():
    assessment, _ = apply_safety_check(_clf("Normal", 0.98, tumor_prob=0.02))
    assert assessment.risk_level == "low"
    assert assessment.clinical_action == "결과 참고 가능"


def test_disclaimer_always_present():
    for conf in [0.70, 0.88, 0.96]:
        _, disclaimer = apply_safety_check(_clf("Tumor", conf))
        assert "전문의" in disclaimer
        assert disclaimer == DISCLAIMER
