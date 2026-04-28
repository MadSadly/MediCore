import pandas as pd
import numpy as np  # <--- 이 줄을 반드시 추가해주세요!
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import confusion_matrix, roc_curve, auc, ConfusionMatrixDisplay
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

class ColorectalModelManager:
    def __init__(self, data_path="AI/GW/dataset/colorectal_cancer_dataset.csv"):
        self.data_path = data_path
        self.preprocessor = None
        self.best_model = None

    def run_pipeline(self):
        # 1. 데이터 로드 및 분할
        df = pd.read_csv(self.data_path)
        X = df.drop(columns=['Patient_ID', 'Survival_Prediction'])
        y = df['Survival_Prediction'].map({'Yes': 1, 'No': 0})
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # 2. 전처리기 구축
        numeric_features = ['Age', 'Tumor_Size_mm', 'Healthcare_Costs', 'Incidence_Rate_per_100K', 'Mortality_Rate_per_100K']
        categorical_features = [col for col in X.columns if col not in numeric_features]
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])

        # 3. 데이터 변환 및 SMOTE 적용 (훈련 데이터만)
        X_train_processed = self.preprocessor.fit_transform(X_train)
        X_test_processed = self.preprocessor.transform(X_test)

        smote = SMOTE(random_state=42)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train_processed, y_train)

        # 4. 모델 평가 및 시각화
        self._evaluate_models(X_train_resampled, y_train_resampled, X_test_processed, y_test)

        # 5. 최적화 및 저장
        self._optimize_and_save(X_train_resampled, y_train_resampled)

    def _evaluate_models(self, X_train, y_train, X_test, y_test):
        models = {
            "Random Forest": RandomForestClassifier(random_state=42),
            "XGBoost": XGBClassifier(eval_metric='logloss', random_state=42),
            "LightGBM": LGBMClassifier(random_state=42, force_row_wise=True)
        }

        # 1행 4열의 거대한 도화지(Figure)와 각각의 영역(axes) 생성
        fig, axes = plt.subplots(2, 2, figsize=(12, 12))
        # [핵심] 2차원 배열을 1차원으로 평탄화 해줍니다. (0번, 1번, 2번, 3번 인덱스로 접근 가능)
        axes = axes.flatten()
        roc_data = []

        for i, (name, model) in enumerate(models.items()):
            # 데이터 변환 (LightGBM 경고 방지)
            X_train_arr = np.array(X_train)
            X_test_arr = np.array(X_test)
            y_train_arr = np.array(y_train)

            # 모델 학습
            model.fit(X_train_arr, y_train_arr)

            # ROC 데이터 임시 저장
            y_pred_proba = model.predict_proba(X_test_arr)[:, 1]
            fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
            roc_data.append((name, fpr, tpr, auc(fpr, tpr)))

            # Confusion Matrix를 각각 지정된 구역(ax=axes[i])에 그리기
            y_pred = model.predict(X_test_arr)
            cm = confusion_matrix(y_test, y_pred)
            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['No(0)', 'Yes(1)'])
            disp.plot(cmap='Blues', ax=axes[i])
            axes[i].set_title(f'{name} CM')

        # 마지막 4번째 구역(axes[3])에 모든 ROC 커브를 겹쳐서 그리기
        for name, fpr, tpr, roc_auc in roc_data:
            axes[3].plot(fpr, tpr, label=f'{name} (AUC = {roc_auc:.3f})')

        axes[3].plot([0, 1], [0, 1], 'k--')
        axes[3].set_xlim([0.0, 1.0])
        axes[3].set_ylim([0.0, 1.05])
        axes[3].set_xlabel('False Positive Rate')
        axes[3].set_ylabel('True Positive Rate')
        axes[3].set_title('ROC Curve Comparison')
        axes[3].legend(loc="lower right")

        # 그래프 간격 자동 조절 후 딱 한 번만 화면에 출력!
        plt.tight_layout()
        # plt.show()
        # 화면에 띄우지 않고 프로젝트 폴더에 이미지 파일로 저장
        plt.savefig('AI/GW/model_evaluation_results.png')
        plt.close() # 메모리 확보를 위해 도화지 닫기

    def _optimize_and_save(self, X_train, y_train, save_path='AI/GW/colorectal_cancer_model.pkl'):
        # 최적화 단계에서도 동일하게 XGBoost 파라미터 수정 및 Numpy 배열 적용
        xgb = XGBClassifier(eval_metric='logloss', random_state=42)
        param_grid = {'n_estimators': [100, 200], 'max_depth': [3, 5], 'learning_rate': [0.05, 0.1]}

        grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=5, scoring='roc_auc', n_jobs=-1)
        grid_search.fit(np.array(X_train), np.array(y_train))

        inference_pipeline = ImbPipeline(steps=[
            ('preprocessor', self.preprocessor),
            ('classifier', grid_search.best_estimator_)
        ])

        joblib.dump(inference_pipeline, save_path)
        print(f"최적 파라미터: {grid_search.best_params_}")
        print(f"모델 저장 완료: {save_path}")

if __name__ == "__main__":
    manager = ColorectalModelManager()
    manager.run_pipeline()
