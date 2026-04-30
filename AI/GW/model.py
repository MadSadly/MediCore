import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
import logging
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

logger = logging.getLogger(__name__)

class ColonCancerModel:
    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.pipeline_path = os.path.join(self.model_dir, "colon_cancer_pipeline.pkl")
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        self.pipeline = None
        # 데이터셋 컬럼 정의
        self.feature_cols = [
            'Age', 'Gender', 'Cancer_Stage', 'Tumor_Size_mm', 'Family_History', 'Smoking_History', 
            'Alcohol_Consumption', 'Obesity_BMI', 'Diet_Risk', 'Physical_Activity', 'Diabetes', 
            'Inflammatory_Bowel_Disease', 'Genetic_Mutation', 'Screening_History', 'Early_Detection', 
            'Treatment_Type', 'Healthcare_Costs', 'Incidence_Rate_per_100K', 'Mortality_Rate_per_100K', 
            'Urban_or_Rural', 'Economic_Classification', 'Healthcare_Access', 'Insurance_Status'
        ]

    def load_data(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(__file__), "dataset", "colorectal_cancer_dataset.csv")
            
        if not os.path.exists(file_path):
            # 파일이 없을 경우 예시 데이터 생성을 위한 로직 (실제 운영시에는 예외처리)
            logger.warning(f"Dataset not found at {file_path}. Please ensure the CSV is present.")
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        df = pd.read_csv(file_path)
        # 결측치 처리
        df = df.ffill()
        return df

    def perform_eda(self, df):
        """1. 데이터 단계: EDA 및 시각화"""
        results = []
        
        # 타겟 분포 확인 (사망/생존 예측 불균형 확인)
        plt.figure(figsize=(10, 6))
        sns.countplot(x='Survival_Prediction', data=df, hue='Survival_Prediction', palette='viridis', legend=False)
        plt.title('Target Distribution: Survival Prediction (Yes/No)')
        target_plot = os.path.join(self.static_dir, "target_dist.png")
        plt.savefig(target_plot)
        plt.close()
        results.append("static/target_dist.png")

        # 수치형 피처 상관관계
        plt.figure(figsize=(12, 8))
        numeric_df = df.select_dtypes(include=[np.number])
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Numerical Feature Correlation')
        corr_plot = os.path.join(self.static_dir, "correlation.png")
        plt.savefig(corr_plot)
        plt.close()

        return [target_plot, corr_plot]

    def train_pipeline(self, df):
        """2. 모델링 & 3. 최적화 단계"""
        # 데이터 전처리
        X = df.drop(columns=['Patient_ID', 'Survival_Prediction', 'Country'])
        y = df['Survival_Prediction'].map({'Yes': 1, 'No': 0})

        numeric_features = ['Age', 'Tumor_Size_mm', 'Healthcare_Costs', 'Incidence_Rate_per_100K', 'Mortality_Rate_per_100K']
        categorical_features = X.select_dtypes(include=['object']).columns.tolist()

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numeric_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ]
        )

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # 다양한 모델 비교
        models = {
            'RandomForest': RandomForestClassifier(random_state=42),
            'XGBoost': XGBClassifier(eval_metric='logloss', random_state=42),
            'LightGBM': LGBMClassifier(random_state=42)
        }

        comparison_results = {}
        best_f1 = 0
        best_model_name = ""

        # 전처리 및 SMOTE가 포함된 모델 비교를 위해 임시 파이프라인 사용
        for name, model in models.items():
            temp_pipe = ImbPipeline([
                ('preprocessor', preprocessor),
                ('smote', SMOTE(random_state=42)),
                ('classifier', model)
            ])
            temp_pipe.fit(X_train, y_train)
            y_pred = temp_pipe.predict(X_test)
            score = f1_score(y_test, y_pred)
            comparison_results[name] = float(score)
            
            if score > best_f1:
                best_f1 = score
                best_model_name = name

        # 모델 비교 시각화 저장
        plt.figure(figsize=(10, 5))
        plt.bar(comparison_results.keys(), comparison_results.values(), color=['skyblue', 'orange', 'green'])
        plt.title('Model Comparison (F1 Score)')
        plt.ylabel('F1 Score')
        plt.savefig(os.path.join(self.static_dir, "model_comparison.png"))
        plt.close()

        # 3. 최적화: 가장 성능이 좋은 모델로 하이퍼파라미터 튜닝
        best_clf = models[best_model_name]
        
        final_pipeline = ImbPipeline([
            ('preprocessor', preprocessor),
            ('smote', SMOTE(random_state=42)),
            ('classifier', best_clf)
        ])

        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [None, 5, 10]
        }

        grid_search = GridSearchCV(final_pipeline, param_grid, cv=3, scoring='f1', n_jobs=1) # 1 for stability
        grid_search.fit(X_train, y_train)

        # 최적 모델 저장
        self.pipeline = grid_search.best_estimator_
        joblib.dump(self.pipeline, self.pipeline_path)
        
        # 전처리 과정 시각화 (피처 중요도 등)
        self._save_feature_importance(grid_search.best_estimator_, X, best_model_name)

        return comparison_results, best_model_name, self.pipeline_path

    def _save_feature_importance(self, pipeline, X, model_name):
        try:
            if hasattr(pipeline.named_steps['classifier'], 'feature_importances_'):
                importances = pipeline.named_steps['classifier'].feature_importances_
                # 원핫인코딩으로 인해 늘어난 피처 이름 가져오기
                cat_encoder = pipeline.named_steps['preprocessor'].named_transformers_['cat']
                cat_features = cat_encoder.get_feature_names_out().tolist()
                num_features = pipeline.named_steps['preprocessor'].named_transformers_['num'].get_feature_names_out().tolist()
                all_features = num_features + cat_features
                
                feat_imp = pd.Series(importances, index=all_features).sort_values(ascending=False).head(10)
                plt.figure(figsize=(10, 6))
                feat_imp.plot(kind='barh')
                plt.title(f'Top 10 Feature Importances ({model_name})')
                plt.savefig(os.path.join(self.static_dir, "feature_importance.png"))
                plt.close()
        except Exception as e:
            logger.warning(f"Could not save feature importance: {e}")

    def predict(self, features_list):
        if self.pipeline is None:
            if os.path.exists(self.pipeline_path):
                self.pipeline = joblib.load(self.pipeline_path)
            else:
                raise ValueError("모델 파이프라인이 학습되지 않았습니다.")
        
        test_df = pd.DataFrame([features_list], columns=self.feature_cols)
        pred = self.pipeline.predict(test_df)[0]
        prob = self.pipeline.predict_proba(test_df)[0][1]
        
        return int(pred), float(prob)

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    model = ColonCancerModel()
    
    print("1. 데이터 로드 중...")
    data = model.load_data()
    
    print("2. EDA 수행 및 시각화 저장 중...")
    model.perform_eda(data)
    
    print("3. 모델 학습 및 파이프라인 최적화 시작...")
    comparison, best_model, path = model.train_pipeline(data)
    
    print(f"학습 완료! 최적 모델: {best_model}")
    print(f"모델 저장 경로: {path}")