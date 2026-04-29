"""
신부전 AI 진단 모델 (TabNet 기반)

데이터: Kaggle CKD Dataset (20,538개)
모델:   TabNet 5단계 분류
타겟:   원본 eGFR → KDIGO 기준 5단계
피처:   임상 수치 + 범주형
"""

import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.impute import SimpleImputer
from imblearn.over_sampling import SMOTE
from pytorch_tabnet.tab_model import TabNetClassifier
import torch

warnings.filterwarnings('ignore')

# ── 경로 ──────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
DATA_PATH    = BASE_DIR / "datasets/kidney_disease_dataset.csv"
MODEL_DIR    = BASE_DIR / "models/kidney"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH   = MODEL_DIR / "tabnet_stage.pkl"
SCALER_PATH  = MODEL_DIR / "scaler_stage.pkl"
IMPUTER_PATH = MODEL_DIR / "imputer_stage.pkl"
ENCODER_PATH = MODEL_DIR / "encoder_stage.pkl"

# ── 컬럼 매핑 ─────────────────────────────────────────────────
KAGGLE_TO_STD = {
    'Age of the patient':                    'age',
    'Blood pressure (mm/Hg)':               'bp',
    'Specific gravity of urine':            'sg',
    'Albumin in urine':                     'al',
    'Sugar in urine':                       'su',
    'Random blood glucose level (mg/dl)':   'bgr',
    'Blood urea (mg/dl)':                   'bu',
    'Serum creatinine (mg/dl)':             'sc',
    'Sodium level (mEq/L)':                 'sod',
    'Potassium level (mEq/L)':              'pot',
    'Hemoglobin level (gms)':               'hemo',
    'Packed cell volume (%)':               'pcv',
    'White blood cell count (cells/cumm)':  'wc',
    'Red blood cell count (millions/cumm)': 'rc',
    'Red blood cells in urine':             'rbc',
    'Pus cells in urine':                   'pc',
    'Pus cell clumps in urine':             'pcc',
    'Bacteria in urine':                    'ba',
    'Hypertension (yes/no)':                'htn',
    'Diabetes mellitus (yes/no)':           'dm',
    'Coronary artery disease (yes/no)':     'cad',
    'Appetite (good/poor)':                 'appet',
    'Pedal edema (yes/no)':                 'pe',
    'Anemia (yes/no)':                      'ane',
    'Estimated Glomerular Filtration Rate (eGFR)': 'egfr',
}

# ── 피처 (eGFR 제외) ──────────────────────────────────────────
NUMERIC_COLS = [
    'age', 'bp', 'sg', 'al', 'su', 'bgr', 'bu', 'sc',
    'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc', 'egfr',
]
CATEGORICAL_COLS = [
    'rbc', 'pc', 'pcc', 'ba', 'htn', 'dm',
    'cad', 'appet', 'pe', 'ane',
]
FEATURE_COLS = NUMERIC_COLS + CATEGORICAL_COLS
TARGET_COL   = 'ckd_stage'
STAGE_LABELS = ['Normal_Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5']

STAGE_INFO = {
    'Normal_Stage1': {'desc': '정상 또는 CKD 1단계 (eGFR ≥ 90)',        'severity': 'normal',   'dialysis': False},
    'Stage2':        {'desc': 'CKD 2단계 - 경미한 신기능 저하 (60~89)',  'severity': 'mild',     'dialysis': False},
    'Stage3':        {'desc': 'CKD 3단계 - 중등도 신기능 저하 (30~59)', 'severity': 'moderate', 'dialysis': False},
    'Stage4':        {'desc': 'CKD 4단계 - 중증 신기능 저하 (15~29)',   'severity': 'severe',   'dialysis': False},
    'Stage5':        {'desc': 'CKD 5단계 - 신부전, 투석 필요 (< 15)',   'severity': 'critical', 'dialysis': True},
}


def assign_stage(egfr: float) -> str:
    if pd.isna(egfr):  return 'Normal_Stage1'
    if egfr >= 90:     return 'Normal_Stage1'
    elif egfr >= 60:   return 'Stage2'
    elif egfr >= 30:   return 'Stage3'
    elif egfr >= 15:   return 'Stage4'
    else:              return 'Stage5'


# ── 전처리 ────────────────────────────────────────────────────
def preprocess(df, fit=True,
               imputer=None, scaler=None,
               cat_encoders=None, label_enc=None):
    df = df.copy()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                               .str.strip()
                               .str.lower()
                               .replace({'?': np.nan, 'nan': np.nan})
                               .fillna('unknown'))

    if fit:
        cat_encoders = {}
        for col in CATEGORICAL_COLS:
            if col in df.columns:
                enc = LabelEncoder()
                df[col] = enc.fit_transform(df[col].astype(str))
                cat_encoders[col] = enc
    else:
        for col in CATEGORICAL_COLS:
            if col in df.columns and col in cat_encoders:
                enc = cat_encoders[col]
                df[col] = df[col].astype(str).map(
                    lambda x: enc.transform([x])[0]
                    if x in enc.classes_ else 0
                )

    feature_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feature_cols].values.astype(np.float32)

    if fit:
        imputer = SimpleImputer(strategy='median')
        X = imputer.fit_transform(X)
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
    else:
        X = imputer.transform(X)
        X = scaler.transform(X)

    y = None
    if TARGET_COL in df.columns:
        if fit:
            label_enc = LabelEncoder()
            label_enc.fit(STAGE_LABELS)
            y = label_enc.transform(df[TARGET_COL])
        else:
            y = label_enc.transform(df[TARGET_COL])

    return X, y, imputer, scaler, cat_encoders, label_enc, feature_cols


# ── 학습 ─────────────────────────────────────────────────────
def train():
    print("=" * 60)
    print("🏥 신부전 TabNet 모델 학습")
    print("   데이터: Kaggle CKD Dataset (20,538개)")
    print("   타겟:   원본 eGFR → KDIGO 5단계")
    print("=" * 60)

    df = pd.read_csv(DATA_PATH)
    df = df.rename(columns=KAGGLE_TO_STD)
    df['egfr'] = pd.to_numeric(df['egfr'], errors='coerce')
    df[TARGET_COL] = df['egfr'].apply(assign_stage)

    print(f"\n   데이터 크기: {df.shape}")
    print(f"   단계별 분포:")
    for stage in STAGE_LABELS:
        count = (df[TARGET_COL] == stage).sum()
        print(f"     {stage:15s}: {count}개")

    X, y, imputer, scaler, cat_encoders, label_enc, feature_cols = \
        preprocess(df, fit=True)

    print(f"\n   피처 수: {len(feature_cols)} (eGFR 제외)")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\n⚖️  SMOTE 오버샘플링...")
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)
    unique, counts = np.unique(y_train, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   {label_enc.classes_[u]:15s}: {c}개")

    print("\n🔧 TabNet 학습 중...")
    model = TabNetClassifier(
        n_d=64, n_a=64,
        n_steps=5,
        gamma=1.5,
        n_independent=3,
        n_shared=3,
        optimizer_fn=torch.optim.Adam,
        optimizer_params=dict(lr=1e-3, weight_decay=1e-5),
        scheduler_params=dict(step_size=30, gamma=0.9),
        scheduler_fn=torch.optim.lr_scheduler.StepLR,
        mask_type='sparsemax',
        verbose=10,
        device_name='cpu',
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_name=['val'],
        eval_metric=['accuracy'],
        max_epochs=300,
        patience=30,
        batch_size=512,
        virtual_batch_size=256,
        weights=1,
    )

    y_pred = model.predict(X_val)
    acc    = accuracy_score(y_val, y_pred)

    print(f"\n✅ 검증 정확도: {acc:.4f}")
    print(classification_report(
        y_val, y_pred, target_names=label_enc.classes_))

    with open(MODEL_PATH,  'wb') as f: pickle.dump(model, f)
    with open(SCALER_PATH, 'wb') as f: pickle.dump(scaler, f)
    with open(IMPUTER_PATH,'wb') as f: pickle.dump(imputer, f)
    with open(ENCODER_PATH,'wb') as f:
        pickle.dump({
            'cat':      cat_encoders,
            'label':    label_enc,
            'features': feature_cols,
        }, f)

    print(f"\n💾 모델 저장 완료: {MODEL_DIR}")
    return acc


# ── 추론 클래스 ───────────────────────────────────────────────
class KidneyPredictor:

    def __init__(self):
        self._load()

    def _load(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"모델 없음: {MODEL_PATH}\n"
                "먼저 python model.py 로 학습하세요."
            )
        with open(MODEL_PATH,  'rb') as f: self.model        = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f: self.scaler       = pickle.load(f)
        with open(IMPUTER_PATH,'rb') as f: self.imputer      = pickle.load(f)
        with open(ENCODER_PATH,'rb') as f:
            enc = pickle.load(f)
            self.cat_encoders  = enc['cat']
            self.label_encoder = enc['label']
            self.feature_cols  = enc['features']
        print("✅ 신부전 모델 로드 완료")

    def predict(self, input_data: dict) -> dict:
        data = {k: v for k, v in input_data.items()
                if k != 'egfr'}

        df = pd.DataFrame([data])

        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        for col in CATEGORICAL_COLS:
            if col in df.columns and col in self.cat_encoders:
                df[col] = (df[col].astype(str)
                                   .str.strip()
                                   .str.lower())
                enc = self.cat_encoders[col]
                df[col] = df[col].map(
                    lambda x: enc.transform([x])[0]
                    if x in enc.classes_ else 0
                )

        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = np.nan

        X = df[self.feature_cols].values.astype(np.float32)
        X = self.imputer.transform(X)
        X = self.scaler.transform(X)

        pred_idx   = self.model.predict(X)[0]
        pred_proba = self.model.predict_proba(X)[0]
        prediction = self.label_encoder.classes_[pred_idx]
        confidence = float(pred_proba[pred_idx])
        info       = STAGE_INFO[prediction]

        return {
            "prediction":        prediction,
            "confidence":        round(confidence, 4),
            "description":       info['desc'],
            "severity":          info['severity'],
            "dialysis_required": info['dialysis'],
            "probabilities": {
                cls: round(float(p), 4)
                for cls, p in zip(
                    self.label_encoder.classes_, pred_proba)
            },
        }


if __name__ == "__main__":
    train()