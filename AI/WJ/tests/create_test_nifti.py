"""
테스트용 합성 NIfTI 파일 생성기.

BraTS-like (종양) 10건 + OASIS-like (정상) 10건을 생성한다.
전처리 파이프라인 검증 목적이며, 실제 의료 데이터와 통계적 특성을 흉내낸다.

사용법:
    python -m WJ.tests.create_test_nifti
    python -m WJ.tests.create_test_nifti --out-dir ./test_data --n 5
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import nibabel as nib
import numpy as np


# ─── 실제 MRI 파라미터 기준 ──────────────────────────────────────────────────

# BraTS 2020: 1mm isotropic, 240x240x155, skull-stripped
BRATS_SHAPE = (240, 240, 155)
BRATS_SPACING = (1.0, 1.0, 1.0)

# OASIS-1: ~1mm isotropic, 256x256x128, skull 있음
OASIS_SHAPE = (256, 256, 128)
OASIS_SPACING = (1.0, 1.0, 1.25)


def _make_affine(spacing: tuple[float, float, float]) -> np.ndarray:
    """RAS 기준 diagonal affine 행렬 생성."""
    aff = np.eye(4)
    aff[0, 0] = spacing[0]
    aff[1, 1] = spacing[1]
    aff[2, 2] = spacing[2]
    return aff


def _gaussian_blob(shape: tuple, center: tuple, sigma: float, amplitude: float) -> np.ndarray:
    """가우시안 blob — 종양/뇌 구조 시뮬레이션용."""
    zz, yy, xx = np.ogrid[:shape[0], :shape[1], :shape[2]]
    dist_sq = ((zz - center[0]) / sigma) ** 2 + ((yy - center[1]) / sigma) ** 2 + ((xx - center[2]) / sigma) ** 2
    return amplitude * np.exp(-dist_sq / 2).astype(np.float32)


def make_tumor_nifti(seed: int = 0) -> nib.Nifti1Image:
    """
    BraTS-like 종양 NIfTI 생성.
    - skull-stripped (뇌 마스크 내부 신호, 외부 0)
    - 종양 코어: 고신호 타원형 blob
    - 주변 부종: 중간 신호 넓은 blob
    """
    rng = np.random.default_rng(seed)
    shape = BRATS_SHAPE
    vol = np.zeros(shape, dtype=np.float32)

    # 뇌 마스크 (타원형)
    cx, cy, cz = shape[0] // 2, shape[1] // 2, shape[2] // 2
    rx, ry, rz = shape[0] * 0.38, shape[1] * 0.38, shape[2] * 0.42
    zz, yy, xx = np.ogrid[:shape[0], :shape[1], :shape[2]]
    brain_mask = ((zz - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 + ((xx - cz) / rz) ** 2 <= 1.0

    # 배경 노이즈 (뇌 내부)
    vol[brain_mask] = rng.normal(0.4, 0.08, brain_mask.sum()).astype(np.float32)

    # 백질/회백질 구분 (간단한 2층 구조)
    inner_mask = ((zz - cx) / (rx * 0.6)) ** 2 + ((yy - cy) / (ry * 0.6)) ** 2 + ((xx - cz) / (rz * 0.65)) ** 2 <= 1.0
    vol[inner_mask] = rng.normal(0.6, 0.06, inner_mask.sum()).astype(np.float32)

    # 종양 위치 (우상단 사분면에 편향)
    tumor_x = int(cx + rng.uniform(0.1, 0.3) * rx)
    tumor_y = int(cy + rng.uniform(-0.2, 0.2) * ry)
    tumor_z = int(cz + rng.uniform(-0.1, 0.2) * rz)

    # 부종 (T2 high signal)
    vol += _gaussian_blob(shape, (tumor_x, tumor_y, tumor_z), sigma=18, amplitude=0.4)
    # 종양 코어 (T1 contrast-enhanced)
    vol += _gaussian_blob(shape, (tumor_x, tumor_y, tumor_z), sigma=8, amplitude=0.5)
    # 괴사 영역 (T1 low signal)
    necrosis = _gaussian_blob(shape, (tumor_x, tumor_y, tumor_z), sigma=3, amplitude=-0.3)
    vol += necrosis

    # skull-stripped: 뇌 외부 0
    vol[~brain_mask] = 0.0
    vol = np.clip(vol, 0.0, 1.5)

    return nib.Nifti1Image(vol, _make_affine(BRATS_SPACING))


def make_normal_nifti(seed: int = 0) -> nib.Nifti1Image:
    """
    OASIS-like 정상 NIfTI 생성.
    - skull 포함 (skull strip 전 raw MRI)
    - 균일한 뇌 신호, 두개골 고신호
    - 종양 없음
    """
    rng = np.random.default_rng(seed + 1000)
    shape = OASIS_SHAPE
    vol = np.zeros(shape, dtype=np.float32)

    cx, cy, cz = shape[0] // 2, shape[1] // 2, shape[2] // 2
    rx, ry, rz = shape[0] * 0.40, shape[1] * 0.40, shape[2] * 0.44
    zz, yy, xx = np.ogrid[:shape[0], :shape[1], :shape[2]]

    # 두개골 (shell)
    skull_outer = ((zz - cx) / (rx * 1.08)) ** 2 + ((yy - cy) / (ry * 1.08)) ** 2 + ((xx - cz) / (rz * 1.06)) ** 2 <= 1.0
    skull_inner = ((zz - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 + ((xx - cz) / rz) ** 2 <= 1.0
    skull_mask = skull_outer & ~skull_inner
    vol[skull_mask] = rng.normal(0.85, 0.05, skull_mask.sum()).astype(np.float32)

    # 뇌 (두개골 내부)
    brain_mask = skull_inner.copy()
    vol[brain_mask] = rng.normal(0.45, 0.07, brain_mask.sum()).astype(np.float32)

    # 백질
    inner_mask = ((zz - cx) / (rx * 0.55)) ** 2 + ((yy - cy) / (ry * 0.55)) ** 2 + ((xx - cz) / (rz * 0.60)) ** 2 <= 1.0
    vol[inner_mask] = rng.normal(0.65, 0.05, inner_mask.sum()).astype(np.float32)

    # CSF (뇌실 — 저신호)
    for dx, dy, dz in [(-0.12, 0, 0), (0.12, 0, 0)]:
        ventricle_center = (int(cx + dx * rx), int(cy + dy * ry), int(cz + dz * rz))
        vol -= _gaussian_blob(shape, ventricle_center, sigma=5, amplitude=0.25)

    vol = np.clip(vol, 0.0, 1.2)

    return nib.Nifti1Image(vol, _make_affine(OASIS_SPACING))


def generate_dataset(out_dir: str | Path, n: int = 10, verbose: bool = True) -> dict[str, list[str]]:
    """
    종양/정상 NIfTI 파일 생성 후 저장.

    Args:
        out_dir: 저장 루트 경로
        n: 각 클래스 파일 수 (기본 10)

    Returns:
        {"tumor": [...paths], "normal": [...paths]}
    """
    out_dir = Path(out_dir)
    tumor_dir = out_dir / "tumor"
    normal_dir = out_dir / "normal"
    tumor_dir.mkdir(parents=True, exist_ok=True)
    normal_dir.mkdir(parents=True, exist_ok=True)

    tumor_paths, normal_paths = [], []

    for i in range(n):
        # 종양 (BraTS-like, skull-stripped)
        t_path = tumor_dir / f"brats_synthetic_{i:03d}.nii.gz"
        nib.save(make_tumor_nifti(seed=i), t_path)
        tumor_paths.append(str(t_path))
        if verbose:
            print(f"[tumor {i+1:2d}/{n}] {t_path.name}  skull_strip=False")

        # 정상 (OASIS-like, skull 있음)
        n_path = normal_dir / f"oasis_synthetic_{i:03d}.nii.gz"
        nib.save(make_normal_nifti(seed=i), n_path)
        normal_paths.append(str(n_path))
        if verbose:
            print(f"[normal {i+1:2d}/{n}] {n_path.name}  skull_strip=True")

    if verbose:
        print(f"\n생성 완료: 종양 {n}건, 정상 {n}건 → {out_dir}")
        print("\n테스트 명령어 예시:")
        print(f"  curl -X POST http://localhost:8000/ai/brain/diagnose \\")
        print(f"    -F 'file=@{tumor_paths[0]}' -F 'skull_strip=false'")
        print(f"  curl -X POST http://localhost:8000/ai/brain/diagnose \\")
        print(f"    -F 'file=@{normal_paths[0]}' -F 'skull_strip=true'")

    return {"tumor": tumor_paths, "normal": normal_paths}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="테스트용 합성 MRI NIfTI 파일 생성")
    parser.add_argument("--out-dir", default="AI/WJ/tests/test_data", help="저장 경로 (기본: AI/WJ/tests/test_data)")
    parser.add_argument("--n", type=int, default=10, help="각 클래스 파일 수 (기본 10)")
    args = parser.parse_args()

    generate_dataset(args.out_dir, n=args.n)
