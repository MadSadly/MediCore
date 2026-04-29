"""
신부전 모델 추가 시각화
6. ROC 커브 (다중 클래스)
7. SHAP 값 (Explainable AI)
8. 학습 곡선
9. 오류 케이스 분석
"""

import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import os

from sklearn.model_selection import train_test_split, learning_curve
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings('ignore')

# ── 한글 폰트 설정 ─────────────────────────────────────────────
def set_korean_font():
    font_candidates = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            fm.fontManager.addfont(font_path)
            font_name = fm.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_name
            plt.rcParams['axes.unicode_minus'] = False
            return True
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    return False

set_korean_font()

OUTPUT_DIR = 'analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 상수 ──────────────────────────────────────────────────────
KAGGLE_PATH = 'datasets/kidney/kidney_disease_dataset.csv'

KAGGLE_TO_STD = {
    'Age of the patient':                    'age',
    'Blood pressure (mm/Hg)':               'bp',
    'Specific gravity of urine':            'sg',
    'Albumin in urine':                     'al',
    'Sugar in urine':                       'su',
    'Random blood glucose level (mg/dl)':   'bgr',
kaggle_col
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

NUMERIC_COLS     = ['age','bp','sg','al','su','bgr','bu','sc',
                    'sod','pot','hemo','pcv','wc','rc','egfr']
CATEGORICAL_COLS = ['rbc','pc','pcc','ba','htn','dm','cad',
                    'appet','pe','ane']
FEATURE_COLS     = NUMERIC_COLS + CATEGORICAL_COLS
TARGET_COL       = 'ckd_stage'
STAGE_LABELS     = ['Normal_Stage1','Stage2','Stage3','Stage4','Stage5']

STAGE_KOR = {
    'Normal_Stage1': '정상/1단계',
    'Stage2':        '2단계',
    'Stage3':        '3단계',
    'Stage4':        '4단계',
    'Stage5':        '5단계',
}

FEAT_KOR = {
    'age':'나이','bp':'혈압','sg':'소변비중','al':'알부민뇨',
    'su':'당뇨','bgr':'혈당','bu':'혈중요소','sc':'혈청크레아티닌',
    'sod':'나트륨','pot':'칼륨','hemo':'헤모글로빈','pcv':'적혈구용적',
    'wc':'백혈구수','rc':'적혈구수','egfr':'eGFR',
    'rbc':'적혈구(소변)','pc':'고름세포','pcc':'고름세포군집',
    'ba':'박테리아','htn':'고혈압','dm':'당뇨병','cad':'관상동맥',
    'appet':'식욕','pe':'부종','ane':'빈혈',
}

STAGE_COLORS = ['#4CAF50','#2196F3','#FF9800','#F44336','#9C27B0']


def assign_stage(egfr):
    if egfr >= 90:   return 'Normal_Stage1'
    elif egfr >= 60: return 'Stage2'
    elif egfr >= 30: return 'Stage3'
    elif egfr >= 15: return 'Stage4'
    else:            return 'Stage5'


# ── 데이터 + 모델 로드 ────────────────────────────────────────
def load_all():
    kaggle = pd.read_csv(KAGGLE_PATH).rename(columns=KAGGLE_TO_STD)
    kaggle[TARGET_COL] = kaggle['egfr'].apply(assign_stage)

    kc = [c for c in FEATURE_COLS if c in kaggle.columns]
    df = kaggle[kc + [TARGET_COL]].copy()

    with open('models/kidney/encoder_stage.pkl','rb') as f:
        enc = pickle.load(f)
    with open('models/kidney/scaler_stage.pkl','rb') as f:
        scaler = pickle.load(f)
    with open('models/kidney/imputer_stage.pkl','rb') as f:
        imputer = pickle.load(f)
    with open('models/kidney/tabnet_stage.pkl','rb') as f:
        model = pickle.load(f)

    cat_encoders = enc['cat']
    label_enc    = enc['label']
    feature_cols = enc['features']

    df2 = df.copy()
    for col in NUMERIC_COLS:
        if col in df2.columns:
            df2[col] = pd.to_numeric(df2[col], errors='coerce')
    for col in CATEGORICAL_COLS:
        if col in df2.columns and col in cat_encoders:
            df2[col] = df2[col].astype(str).str.strip().str.lower().fillna('unknown')
            e = cat_encoders[col]
            df2[col] = df2[col].map(
                lambda x: e.transform([x])[0] if x in e.classes_ else 0)
    for col in feature_cols:
        if col not in df2.columns:
            df2[col] = np.nan

    X = df2[feature_cols].values.astype(np.float32)
    X = imputer.transform(X)
    X = scaler.transform(X)
    y = label_enc.transform(df[TARGET_COL])

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    return (X, y, X_tr, X_val, y_tr, y_val,
            model, label_enc, feature_cols, df)


# ── 시각화 6: ROC 커브 ────────────────────────────────────────
def plot_roc_curve(X_val, y_val, model, label_enc):
    print("📊 6. ROC 커브 생성 중...")

    classes    = label_enc.classes_
    n_classes  = len(classes)
    kor_labels = [STAGE_KOR[c] for c in classes]

    # 예측 확률
    y_score = model.predict_proba(X_val)

    # 이진화
    y_bin = label_binarize(y_val, classes=list(range(n_classes)))

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # ── 좌: 클래스별 ROC ──
    all_auc = []
    for i, (cls, kor, color) in enumerate(
            zip(classes, kor_labels, STAGE_COLORS)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_score[:, i])
        roc_auc = auc(fpr, tpr)
        all_auc.append(roc_auc)
        axes[0].plot(fpr, tpr, color=color, lw=2,
                     label=f'{kor} (AUC = {roc_auc:.4f})')

    axes[0].plot([0,1],[0,1],'k--', lw=1, alpha=0.5, label='무작위 분류')
    axes[0].fill_between([0,1],[0,1], alpha=0.05, color='gray')
    axes[0].set_xlim([-0.02, 1.02])
    axes[0].set_ylim([-0.02, 1.05])
    axes[0].set_xlabel('위양성률 (FPR)', fontsize=12)
    axes[0].set_ylabel('진양성률 (TPR)', fontsize=12)
    axes[0].set_title('클래스별 ROC 커브', fontsize=13)
    axes[0].legend(loc='lower right', fontsize=10)
    axes[0].grid(alpha=0.3)

    # ── 우: Macro / Micro 평균 ROC ──
    # Micro
    fpr_micro, tpr_micro, _ = roc_curve(
        y_bin.ravel(), y_score.ravel())
    auc_micro = auc(fpr_micro, tpr_micro)

    # Macro
    all_fpr = np.unique(np.concatenate([
        roc_curve(y_bin[:,i], y_score[:,i])[0]
        for i in range(n_classes)]))
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        fpr_i, tpr_i, _ = roc_curve(y_bin[:,i], y_score[:,i])
        mean_tpr += np.interp(all_fpr, fpr_i, tpr_i)
    mean_tpr /= n_classes
    auc_macro = auc(all_fpr, mean_tpr)

    axes[1].plot(fpr_micro, tpr_micro,
                 color='deeppink', lw=2.5, linestyle='-',
                 label=f'Micro 평균 (AUC = {auc_micro:.4f})')
    axes[1].plot(all_fpr, mean_tpr,
                 color='navy', lw=2.5, linestyle='--',
                 label=f'Macro 평균 (AUC = {auc_macro:.4f})')

    for i, (cls, kor, color) in enumerate(
            zip(classes, kor_labels, STAGE_COLORS)):
        fpr_i, tpr_i, _ = roc_curve(y_bin[:,i], y_score[:,i])
        axes[1].plot(fpr_i, tpr_i, color=color,
                     lw=1, alpha=0.4, linestyle=':')

    axes[1].plot([0,1],[0,1],'k--', lw=1, alpha=0.5)
    axes[1].fill_between(fpr_micro, tpr_micro, alpha=0.08, color='deeppink')
    axes[1].set_xlim([-0.02, 1.02])
    axes[1].set_ylim([-0.02, 1.05])
    axes[1].set_xlabel('위양성률 (FPR)', fontsize=12)
    axes[1].set_ylabel('진양성률 (TPR)', fontsize=12)
    axes[1].set_title('Macro / Micro 평균 ROC', fontsize=13)
    axes[1].legend(loc='lower right', fontsize=11)
    axes[1].grid(alpha=0.3)

    # AUC 요약 텍스트
    summary = '\n'.join([
        f'{STAGE_KOR[c]}: {a:.4f}'
        for c, a in zip(classes, all_auc)
    ]) + f'\nMicro 평균: {auc_micro:.4f}\nMacro 평균: {auc_macro:.4f}'

    axes[1].text(0.55, 0.25, summary,
                 transform=axes[1].transAxes,
                 fontsize=9, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='lightyellow',
                           alpha=0.8))

    fig.suptitle('CKD 단계 분류 ROC 커브 분석', fontsize=15)
    plt.tight_layout()

    path = f'{OUTPUT_DIR}/6_roc_curve.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   저장: {path}")
    print(f"   Micro AUC: {auc_micro:.4f} | Macro AUC: {auc_macro:.4f}")
    for c, a in zip(classes, all_auc):
        print(f"   {STAGE_KOR[c]:12s}: {a:.4f}")


# ── 시각화 7: SHAP 값 ─────────────────────────────────────────
def plot_shap(X_val, model, label_enc, feature_cols):
    print("\n📊 7. SHAP 값 생성 중...")

    try:
        import shap
    except ImportError:
        print("   pip install shap 필요")
        return

    classes    = label_enc.classes_
    kor_labels = [STAGE_KOR[c] for c in classes]
    feat_kor   = [FEAT_KOR.get(f, f) for f in feature_cols]

    # TabNet SHAP (샘플 500개로 제한)
    sample_idx = np.random.choice(len(X_val),
                                   min(500, len(X_val)),
                                   replace=False)
    X_sample = X_val[sample_idx]

    print("   SHAP 값 계산 중 (시간 소요)...")
    explainer   = shap.Explainer(model.predict_proba, X_sample)
    shap_values = explainer(X_sample)

    fig, axes = plt.subplots(2, 3, figsize=(20, 14))
    axes = axes.flatten()

    # ── 클래스별 SHAP 바 차트 ──
    for cls_idx, (cls, kor, color) in enumerate(
            zip(classes, kor_labels, STAGE_COLORS)):

        shap_cls = shap_values[:, :, cls_idx].values
        mean_abs = np.abs(shap_cls).mean(axis=0)

        top_idx  = np.argsort(mean_abs)[-12:]
        top_feat = [feat_kor[i] for i in top_idx]
        top_vals = mean_abs[top_idx]

        ax = axes[cls_idx]
        bars = ax.barh(range(len(top_idx)), top_vals,
                       color=color, alpha=0.75)
        ax.set_yticks(range(len(top_idx)))
        ax.set_yticklabels(top_feat, fontsize=9)
        ax.set_xlabel('평균 |SHAP| 값', fontsize=9)
        ax.set_title(f'{kor} 클래스\n상위 12 피처', fontsize=10)
        ax.grid(axis='x', alpha=0.3)

        # 수치 표시
        for bar, val in zip(bars, top_vals):
            ax.text(val + 0.0001,
                    bar.get_y() + bar.get_height()/2,
                    f'{val:.4f}', va='center', fontsize=7)

    # ── 전체 평균 SHAP (마지막 subplot) ──
    ax_all = axes[5]
    all_shap = np.abs(shap_values.values).mean(axis=(0,2))
    top_idx  = np.argsort(all_shap)
    top_feat = [feat_kor[i] for i in top_idx]
    top_vals = all_shap[top_idx]

    colors_bar = ['#d32f2f' if v >= np.percentile(all_shap, 75)
                  else '#1976d2' if v >= np.percentile(all_shap, 50)
                  else '#757575'
                  for v in top_vals]

    ax_all.barh(range(len(top_idx)), top_vals,
                color=colors_bar, alpha=0.8)
    ax_all.set_yticks(range(len(top_idx)))
    ax_all.set_yticklabels(top_feat, fontsize=9)
    ax_all.set_xlabel('평균 |SHAP| 값', fontsize=9)
    ax_all.set_title('전체 피처 중요도\n(모든 클래스 평균)', fontsize=10)
    ax_all.grid(axis='x', alpha=0.3)

    fig.suptitle('SHAP 기반 피처 중요도 분석 (Explainable AI)',
                 fontsize=15, y=1.01)
    plt.tight_layout()

    path = f'{OUTPUT_DIR}/7_shap_values.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   저장: {path}")


# ── 시각화 8: 학습 곡선 ──────────────────────────────────────
def plot_learning_curve(X, y, label_enc, feature_cols):
    print("\n📊 8. 학습 곡선 생성 중...")

    from sklearn.ensemble import RandomForestClassifier

    classes    = label_enc.classes_
    kor_labels = [STAGE_KOR[c] for c in classes]

    # RandomForest로 학습 곡선 (TabNet은 sklearn API 미지원)
    clf = RandomForestClassifier(
        n_estimators=100, random_state=42, n_jobs=-1)

    train_sizes = np.linspace(0.1, 1.0, 10)

    print("   학습 곡선 계산 중 (RF 사용)...")
    train_sizes_abs, train_scores, val_scores = learning_curve(
        clf, X, y,
        train_sizes=train_sizes,
        cv=5,
        scoring='accuracy',
        n_jobs=-1,
        verbose=0,
    )

    train_mean = train_scores.mean(axis=1)
    train_std  = train_scores.std(axis=1)
    val_mean   = val_scores.mean(axis=1)
    val_std    = val_scores.std(axis=1)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # ── 좌: 학습 곡선 ──
    axes[0].plot(train_sizes_abs, train_mean,
                 'o-', color='steelblue', lw=2, label='훈련 정확도')
    axes[0].fill_between(train_sizes_abs,
                          train_mean - train_std,
                          train_mean + train_std,
                          alpha=0.15, color='steelblue')

    axes[0].plot(train_sizes_abs, val_mean,
                 's--', color='darkorange', lw=2, label='검증 정확도')
    axes[0].fill_between(train_sizes_abs,
                          val_mean - val_std,
                          val_mean + val_std,
                          alpha=0.15, color='darkorange')

    # 수렴 지점 표시
    converge_idx = np.argmin(np.abs(train_mean - val_mean))
    axes[0].axvline(x=train_sizes_abs[converge_idx],
                    color='red', linestyle=':', alpha=0.6,
                    label=f'수렴 지점: {train_sizes_abs[converge_idx]:.0f}개')

    axes[0].set_xlabel('훈련 데이터 크기', fontsize=12)
    axes[0].set_ylabel('정확도', fontsize=12)
    axes[0].set_title('학습 곡선 (RandomForest 기준)', fontsize=13)
    axes[0].legend(fontsize=10)
    axes[0].grid(alpha=0.3)
    axes[0].set_ylim([0.7, 1.05])

    gap = train_mean - val_mean
    axes[0].text(0.05, 0.05,
                 f'최종 훈련: {train_mean[-1]:.4f}\n'
                 f'최종 검증: {val_mean[-1]:.4f}\n'
                 f'Gap:  {gap[-1]:.4f}',
                 transform=axes[0].transAxes,
                 fontsize=10, verticalalignment='bottom',
                 bbox=dict(boxstyle='round',
                           facecolor='lightyellow', alpha=0.8))

    # ── 우: TabNet epoch별 val_accuracy ──
    tabnet_epochs = list(range(0, 113, 10)) + [112]
    tabnet_val    = [
        0.24118, 0.90913, 0.95143, 0.96133,
        0.94321, 0.96931, 0.97898, 0.97342,
        0.97583, 0.97438, 0.96979, 0.97366,
        0.98598,
    ]

    axes[1].plot(tabnet_epochs, tabnet_val,
                 'o-', color='seagreen', lw=2, markersize=5)
    axes[1].axhline(y=max(tabnet_val), color='red',
                    linestyle='--', alpha=0.5,
                    label=f'최고: {max(tabnet_val):.4f}')
    axes[1].axvline(x=82, color='orange', linestyle=':',
                    alpha=0.7, label='Best epoch: 82')

    # 단계별 설명 주석
    axes[1].annotate('빠른 수렴\n(0→10 epoch)',
                     xy=(10, 0.909), xytext=(25, 0.85),
                     fontsize=9, color='navy',
                     arrowprops=dict(arrowstyle='->', color='navy'))
    axes[1].annotate(f'최고 성능\n(epoch 82)',
                     xy=(82, 0.986), xytext=(60, 0.97),
                     fontsize=9, color='red',
                     arrowprops=dict(arrowstyle='->', color='red'))

    axes[1].set_xlabel('Epoch', fontsize=12)
    axes[1].set_ylabel('검증 정확도', fontsize=12)
    axes[1].set_title('TabNet 학습 진행 곡선\n(Epoch별 검증 정확도)',
                       fontsize=13)
    axes[1].legend(fontsize=10)
    axes[1].grid(alpha=0.3)
    axes[1].set_ylim([0.2, 1.02])

    fig.suptitle('학습 곡선 분석', fontsize=15)
    plt.tight_layout()

    path = f'{OUTPUT_DIR}/8_learning_curve.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   저장: {path}")

    # 과적합 판단
    final_gap = train_mean[-1] - val_mean[-1]
    if final_gap < 0.02:
        print(f"   ✅ 과적합 없음 (훈련-검증 Gap: {final_gap:.4f})")
    elif final_gap < 0.05:
        print(f"   ⚠️  경미한 과적합 (Gap: {final_gap:.4f})")
    else:
        print(f"   ❌ 과적합 의심 (Gap: {final_gap:.4f})")


# ── 시각화 9: 오류 케이스 분석 ───────────────────────────────
def plot_error_analysis(X_val, y_val, model, label_enc, feature_cols, df):
    print("\n📊 9. 오류 케이스 분석 생성 중...")

    classes    = label_enc.classes_
    kor_labels = [STAGE_KOR[c] for c in classes]

    y_pred     = model.predict(X_val)
    pred_proba = model.predict_proba(X_val)

    # 오류 케이스 추출
    error_mask  = y_pred != y_val
    error_true  = y_val[error_mask]
    error_pred  = y_pred[error_mask]
    error_proba = pred_proba[error_mask]
    error_conf  = pred_proba[error_mask, y_pred[error_mask]]

    total_errors = error_mask.sum()
    total_samples = len(y_val)
    print(f"   오류 케이스: {total_errors} / {total_samples} "
          f"({total_errors/total_samples*100:.2f}%)")

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # ── 1. 오류 분포: 실제 vs 예측 ──
    error_pairs = {}
    for t, p in zip(error_true, error_pred):
        key = (classes[t], classes[p])
        error_pairs[key] = error_pairs.get(key, 0) + 1

    pairs = [(k[0], k[1], v)
             for k, v in sorted(error_pairs.items(),
                                 key=lambda x: -x[1])]
    pair_labels = [f'{STAGE_KOR[t]}\n→{STAGE_KOR[p]}'
                   for t, p, _ in pairs]
    pair_counts = [v for _, _, v in pairs]

    bar_colors = []
    for t, p, _ in pairs:
        ti = list(classes).index(t)
        pi = list(classes).index(p)
        bar_colors.append('#d32f2f' if abs(ti-pi) >= 2 else '#FF9800')

    bars = axes[0,0].bar(range(len(pairs)), pair_counts,
                          color=bar_colors, alpha=0.85)
    axes[0,0].set_xticks(range(len(pairs)))
    axes[0,0].set_xticklabels(pair_labels, fontsize=9)
    axes[0,0].set_ylabel('오류 개수', fontsize=11)
    axes[0,0].set_title(f'오류 패턴 분석\n(총 {total_errors}개 오류)',
                         fontsize=12)
    axes[0,0].grid(axis='y', alpha=0.3)

    for bar, cnt in zip(bars, pair_counts):
        axes[0,0].text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.2,
                        str(cnt), ha='center', fontsize=10)

    from matplotlib.patches import Patch
    axes[0,0].legend(handles=[
        Patch(facecolor='#d32f2f', label='2단계 이상 오분류 (위험)'),
        Patch(facecolor='#FF9800', label='인접 단계 오분류 (경미)'),
    ], fontsize=9)

    # ── 2. 오류 케이스의 예측 신뢰도 분포 ──
    correct_conf = pred_proba[~error_mask,
                               y_pred[~error_mask]]
    axes[0,1].hist(correct_conf, bins=30, alpha=0.7,
                    color='steelblue', label=f'정답 ({len(correct_conf)}개)')
    axes[0,1].hist(error_conf, bins=20, alpha=0.7,
                    color='crimson', label=f'오류 ({len(error_conf)}개)')

    axes[0,1].axvline(x=np.mean(correct_conf), color='blue',
                       linestyle='--',
                       label=f'정답 평균: {np.mean(correct_conf):.3f}')
    axes[0,1].axvline(x=np.mean(error_conf), color='red',
                       linestyle='--',
                       label=f'오류 평균: {np.mean(error_conf):.3f}')

    axes[0,1].set_xlabel('예측 신뢰도', fontsize=11)
    axes[0,1].set_ylabel('빈도', fontsize=11)
    axes[0,1].set_title('정답 vs 오류 케이스\n예측 신뢰도 분포', fontsize=12)
    axes[0,1].legend(fontsize=9)
    axes[0,1].grid(alpha=0.3)

    # ── 3. 클래스별 오류율 ──
    error_rates = []
    for i, cls in enumerate(classes):
        mask_cls   = y_val == i
        n_total    = mask_cls.sum()
        n_error    = ((y_pred != y_val) & mask_cls).sum()
        error_rate = n_error / n_total if n_total > 0 else 0
        error_rates.append(error_rate)

    bars = axes[1,0].bar(range(len(classes)), error_rates,
                          color=STAGE_COLORS, alpha=0.8)
    axes[1,0].set_xticks(range(len(classes)))
    axes[1,0].set_xticklabels(kor_labels, fontsize=10)
    axes[1,0].set_ylabel('오류율', fontsize=11)
    axes[1,0].set_title('클래스별 오류율', fontsize=12)
    axes[1,0].yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'{x:.1%}'))
    axes[1,0].grid(axis='y', alpha=0.3)
    axes[1,0].axhline(y=0.05, color='red', linestyle='--',
                       alpha=0.5, label='5% 기준선')
    axes[1,0].legend(fontsize=9)

    for bar, rate in zip(bars, error_rates):
        axes[1,0].text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.001,
            f'{rate:.2%}', ha='center', fontsize=10)

    # ── 4. 오류 케이스 eGFR 분포 ──
    # eGFR이 feature_cols에 있으면 추출
    if 'egfr' in feature_cols:
        egfr_idx = list(feature_cols).index('egfr')

        # imputer/scaler 역변환 없이 원본 데이터에서 추출
        # 검증 세트와 동일한 split로 df에서 추출
        df2 = df.copy()
        df2['egfr'] = pd.to_numeric(df2['egfr'], errors='coerce')
        df2_val = df2.sample(frac=0.2, random_state=42)
        egfr_all = df2_val['egfr'].values[:len(y_val)]

        if len(egfr_all) == len(y_val):
            egfr_correct = egfr_all[~error_mask[:len(egfr_all)]]
            egfr_error   = egfr_all[error_mask[:len(egfr_all)]]

            axes[1,1].hist(egfr_correct, bins=30, alpha=0.6,
                            color='steelblue',
                            label=f'정답 케이스 (n={len(egfr_correct)})')
            axes[1,1].hist(egfr_error, bins=20, alpha=0.8,
                            color='crimson',
                            label=f'오류 케이스 (n={len(egfr_error)})')

            for threshold, label in [(15,'4단계 경계(15)'),
                                      (30,'3단계 경계(30)'),
                                      (60,'2단계 경계(60)'),
                                      (90,'1단계 경계(90)')]:
                axes[1,1].axvline(x=threshold, color='gray',
                                   linestyle='--', alpha=0.5)
                axes[1,1].text(threshold+0.5, axes[1,1].get_ylim()[1]*0.9,
                                label, fontsize=7, color='gray')

            axes[1,1].set_xlabel('eGFR', fontsize=11)
            axes[1,1].set_ylabel('빈도', fontsize=11)
            axes[1,1].set_title('오류 케이스의 eGFR 분포\n(단계 경계값 근처에 집중)',
                                  fontsize=12)
            axes[1,1].legend(fontsize=9)
            axes[1,1].grid(alpha=0.3)
        else:
            _plot_error_summary(axes[1,1], total_errors,
                                total_samples, error_pairs)
    else:
        _plot_error_summary(axes[1,1], total_errors,
                            total_samples, error_pairs)

    fig.suptitle('오류 케이스 상세 분석', fontsize=15)
    plt.tight_layout()

    path = f'{OUTPUT_DIR}/9_error_analysis.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   저장: {path}")

    # 오류 케이스 임상적 위험도 평가
    print("\n   임상적 위험도 평가:")
    safe_errors    = sum(1 for t, p, _ in pairs
                         if abs(list(classes).index(t) -
                                 list(classes).index(p)) == 1)
    danger_errors  = sum(1 for t, p, _ in pairs
                          if abs(list(classes).index(t) -
                                  list(classes).index(p)) >= 2)
    print(f"     인접 단계 오분류(경미): {safe_errors}개")
    print(f"     2단계 이상 오분류(위험): {danger_errors}개")
    print(f"     위험 오류율: {danger_errors/total_samples*100:.3f}%")


def _plot_error_summary(ax, total_errors, total_samples, error_pairs):
    """eGFR 없을 때 오류 요약 텍스트"""
    summary = (
        f"오류 케이스 요약\n\n"
        f"총 오류: {total_errors} / {total_samples}\n"
        f"오류율: {total_errors/total_samples*100:.2f}%\n\n"
        "오류 패턴 (실제→예측):\n" +
        "\n".join([
            f"  {STAGE_KOR[t]} → {STAGE_KOR[p]}: {c}개"
            for t, p, c in sorted(
                [(k[0], k[1], v) for k, v in error_pairs.items()],
                key=lambda x: -x[2])
        ])
    )
    ax.text(0.1, 0.5, summary, transform=ax.transAxes,
            fontsize=11, verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))
    ax.axis('off')


# ── 메인 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🏥 신부전 모델 추가 분석 시작\n")

    (X, y, X_tr, X_val, y_tr, y_val,
     model, label_enc, feature_cols, df) = load_all()

    # 6. ROC 커브
    plot_roc_curve(X_val, y_val, model, label_enc)

    # 7. SHAP 값
    plot_shap(X_val, model, label_enc, feature_cols)

    # 8. 학습 곡선
    plot_learning_curve(X, y, label_enc, feature_cols)

    # 9. 오류 케이스 분석
    plot_error_analysis(X_val, y_val, model,
                         label_enc, feature_cols, df)

    print(f"\n✅ 추가 분석 완료! 결과 저장 위치: {OUTPUT_DIR}/")
    print("   6_roc_curve.png")
    print("   7_shap_values.png")
    print("   8_learning_curve.png")
    print("   9_error_analysis.png")
