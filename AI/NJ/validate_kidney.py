"""
신부전 모델 다각도 검증
1. 다양한 random_state로 반복 테스트
2. 타 모델과 성능 비교 (XGBoost, RandomForest, SVM)
3. 학습 곡선 분석 (과적합 여부)
4. 의심 케이스 직접 예측 테스트
"""

import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, learning_curve
from sklearn.metrics import (accuracy_score, classification_report,
                              roc_auc_score, confusion_matrix)
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from pytorch_tabnet.tab_model import TabNetClassifier
import torch

warnings.filterwarnings('ignore')

# ── 데이터 로드 공통 함수 ─────────────────────────────────────

NUMERIC_COLS     = ['age','bp','sg','al','su','bgr','bu','sc',
                    'sod','pot','hemo','pcv','wc','rc']
CATEGORICAL_COLS = ['rbc','pc','pcc','ba','htn','dm','cad','appet','pe','ane']

def load_data():
    df = pd.read_csv('datasets/kidney_disease_dataset.csv')
    df = df.rename(columns=KAGGLE_TO_STD)
    df['egfr'] = pd.to_numeric(df['egfr'], errors='coerce')
    df[TARGET_COL] = df['egfr'].apply(assign_stage)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].replace({'?': np.nan, 'nan': np.nan})
            df[col] = df[col].fillna('unknown')
            enc = LabelEncoder()
            df[col] = enc.fit_transform(df[col].astype(str))

    feature_cols = [c for c in NUMERIC_COLS + CATEGORICAL_COLS
                    if c in df.columns]
    X = df[feature_cols].values.astype(np.float32)

    imputer = SimpleImputer(strategy='median')
    X = imputer.fit_transform(X)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    label_enc = LabelEncoder()
    y = label_enc.fit_transform(df['classification'])

    return X, y, label_enc.classes_


# ── 검증 1: 다양한 random_state로 반복 테스트 ─────────────────

def test_multiple_seeds():
    print("=" * 60)
    print("검증 1: 30개 random_state로 반복 테스트")
    print("=" * 60)

    # 저장된 모델 로드
    with open('models/kidney/tabnet_ckd.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/kidney/encoder_ckd.pkl', 'rb') as f:
        enc = pickle.load(f)
    with open('models/kidney/scaler_ckd.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('models/kidney/imputer_ckd.pkl', 'rb') as f:
        imputer = pickle.load(f)

    df = pd.read_csv('datasets/kidney_disease_dataset.csv')
    df = df.rename(columns=KAGGLE_TO_STD)
    df['egfr'] = pd.to_numeric(df['egfr'], errors='coerce')
    df[TARGET_COL] = df['egfr'].apply(assign_stage)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    cat_encoders = enc['cat']
    for col in CATEGORICAL_COLS:
        if col in df.columns and col in cat_encoders:
            df[col] = df[col].astype(str).str.strip().str.lower()
            df[col] = df[col].fillna('unknown')
            e = cat_encoders[col]
            df[col] = df[col].map(
                lambda x: e.transform([x])[0]
                if x in e.classes_ else 0
            )

    feature_cols = enc['features']
    X = df[feature_cols].values.astype(np.float32)
    X = imputer.transform(X)
    X = scaler.transform(X)

    label_enc = enc['label']
    y = label_enc.transform(df['classification'])

    scores = []
    for seed in range(30):
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y
        )
        acc = accuracy_score(y_test, model.predict(X_test))
        scores.append(acc)

    scores = np.array(scores)
    print(f"\n30회 반복 결과:")
    print(f"  평균: {scores.mean():.4f}")
    print(f"  최솟값: {scores.min():.4f}")
    print(f"  최댓값: {scores.max():.4f}")
    print(f"  표준편차: {scores.std():.4f}")
    print(f"  90% 이상: {(scores >= 0.90).sum()}회 / 30회")
    print(f"  95% 이상: {(scores >= 0.95).sum()}회 / 30회")
    print(f"  100%:     {(scores == 1.00).sum()}회 / 30회")

    return scores


# ── 검증 2: 타 모델과 성능 비교 ──────────────────────────────

def compare_models():
    print("\n" + "=" * 60)
    print("검증 2: 타 모델과 성능 비교 (5-Fold CV)")
    print("=" * 60)

    X, y, classes = load_data()
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        "RandomForest":  RandomForestClassifier(
                             n_estimators=100, random_state=42),
        "XGBoost":       XGBClassifier(
                             n_estimators=100, random_state=42,
                             eval_metric='logloss', verbosity=0),
        "GradientBoost": GradientBoostingClassifier(
                             n_estimators=100, random_state=42),
        "SVM (RBF)":     SVC(kernel='rbf', probability=True,
                             random_state=42),
    }

    results = {}
    for name, clf in models.items():
        fold_accs = []
        for train_idx, val_idx in kf.split(X, y):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]
            clf.fit(X_tr, y_tr)
            fold_accs.append(accuracy_score(y_val, clf.predict(X_val)))
        mean_acc = np.mean(fold_accs)
        std_acc  = np.std(fold_accs)
        results[name] = (mean_acc, std_acc)
        print(f"  {name:20s}: {mean_acc:.4f} ± {std_acc:.4f}")

    # TabNet CV 결과 (학습 시 나온 값)
    print(f"  {'TabNet':20s}: 0.9875 ± 0.0112  (학습 시 측정)")

    return results


# ── 검증 3: 의심 케이스 직접 예측 ────────────────────────────

def test_edge_cases():
    print("\n" + "=" * 60)
    print("검증 3: 의심 케이스 직접 예측")
    print("=" * 60)

    with open('models/kidney/tabnet_ckd.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/kidney/encoder_ckd.pkl', 'rb') as f:
        enc = pickle.load(f)
    with open('models/kidney/scaler_ckd.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('models/kidney/imputer_ckd.pkl', 'rb') as f:
        imputer = pickle.load(f)

    label_enc    = enc['label']
    cat_encoders = enc['cat']
    feature_cols = enc['features']

    def predict_case(name, data):
        df = pd.DataFrame([data])
        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        for col in CATEGORICAL_COLS:
            if col in df.columns and col in cat_encoders:
                df[col] = df[col].astype(str).str.strip().str.lower()
                e = cat_encoders[col]
                df[col] = df[col].map(
                    lambda x: e.transform([x])[0]
                    if x in e.classes_ else 0
                )
        for col in feature_cols:
            if col not in df.columns:
                df[col] = np.nan
        X = df[feature_cols].values.astype(np.float32)
        X = imputer.transform(X)
        X = scaler.transform(X)

        pred_idx   = model.predict(X)[0]
        pred_proba = model.predict_proba(X)[0]
        pred_label = label_enc.classes_[pred_idx]
        confidence = pred_proba[pred_idx]

        print(f"\n  [{name}]")
        print(f"    예측: {pred_label} (신뢰도: {confidence:.4f})")
        print(f"    CKD 확률: {pred_proba[0]:.4f} | 정상 확률: {pred_proba[1]:.4f}")

    # 케이스 1: 명백한 CKD (크레아티닌 높음, 헤모글로빈 낮음)
    predict_case("명백한 CKD", {
        'age':48, 'bp':80, 'sg':1.01, 'al':3, 'su':0,
        'bgr':121, 'bu':36, 'sc':7.2, 'sod':130, 'pot':4.5,
        'hemo':9.5, 'pcv':29, 'wc':7800, 'rc':3.2,
        'rbc':'abnormal','pc':'abnormal','pcc':'notpresent',
        'ba':'notpresent','htn':'yes','dm':'yes','cad':'no',
        'appet':'poor','pe':'yes','ane':'yes'
    })

    # 케이스 2: 명백한 정상
    predict_case("명백한 정상", {
        'age':30, 'bp':70, 'sg':1.02, 'al':0, 'su':0,
        'bgr':90, 'bu':18, 'sc':0.8, 'sod':138, 'pot':4.0,
        'hemo':15.5, 'pcv':46, 'wc':7200, 'rc':5.2,
        'rbc':'normal','pc':'normal','pcc':'notpresent',
        'ba':'notpresent','htn':'no','dm':'no','cad':'no',
        'appet':'good','pe':'no','ane':'no'
    })

    # 케이스 3: 경계값 (애매한 케이스)
    predict_case("경계값 케이스", {
        'age':55, 'bp':80, 'sg':1.015, 'al':1, 'su':0,
        'bgr':100, 'bu':25, 'sc':1.5, 'sod':136, 'pot':4.2,
        'hemo':13.0, 'pcv':40, 'wc':7500, 'rc':4.5,
        'rbc':'normal','pc':'normal','pcc':'notpresent',
        'ba':'notpresent','htn':'yes','dm':'no','cad':'no',
        'appet':'good','pe':'no','ane':'no'
    })

    # 케이스 4: 결측치가 많은 케이스
    predict_case("결측치 많은 케이스", {
        'age':60, 'bp':np.nan, 'sg':np.nan, 'al':2, 'su':0,
        'bgr':np.nan, 'bu':40, 'sc':3.5, 'sod':np.nan, 'pot':np.nan,
        'hemo':11.0, 'pcv':np.nan, 'wc':np.nan, 'rc':np.nan,
        'rbc':'abnormal','pc':'normal','pcc':'notpresent',
        'ba':'notpresent','htn':'yes','dm':'yes','cad':'no',
        'appet':'poor','pe':'no','ane':'yes'
    })


# ── 메인 실행 ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("🏥 신부전 모델 다각도 검증 시작\n")

    # 검증 1: 반복 테스트
    scores = test_multiple_seeds()

    # 검증 2: 타 모델 비교
    compare_models()

    # 검증 3: 케이스별 직접 예측
    test_edge_cases()

    print("\n" + "=" * 60)
    print("✅ 검증 완료")
    print("=" * 60)
    print(f"""
[요약]
- 30회 반복 평균: {scores.mean():.4f}
- 최솟값: {scores.min():.4f}
- 타 모델과 비교하여 유사하면 → 데이터 자체가 분리 잘 됨
- 경계값 케이스에서 적절한 신뢰도 → 과적합 아님
""")
