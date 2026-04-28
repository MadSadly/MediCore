import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

def train_colon_model(csv_path: str):
    # 1. 로드
    df = pd.read_csv(csv_path)
    
    # 2. EDA (간이 시각화 예시)
    print(f"Dataset Shape: {df.shape}")
    sns.countplot(x='Survival_Prediction', data=df).get_figure().savefig('AI/GW/eda_target.png')

    # 3. 전처리 대상 선정
    X = df[['Age', 'Gender', 'Tumor_Size_mm', 'Family_History', 'Smoking_History', 'Obesity_BMI']]
    y = df['Survival_Prediction'].map({'Yes': 1, 'No': 0})

    numeric_features = ['Age', 'Tumor_Size_mm']
    categorical_features = ['Gender', 'Family_History', 'Smoking_History', 'Obesity_BMI']

    # 4. 파이프라인 구성 (StandardScaler + OneHotEncoder)
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # 5. SMOTE + Model (불균형 해소 포함 최적화)
    model_pipeline = ImbPipeline([
        ('preprocessor', preprocessor),
        ('smote', SMOTE(random_state=42)),
        ('classifier', RandomForestClassifier(random_state=42))
    ])

    # 6. 하이퍼파라미터 튜닝
    param_grid = {
        'classifier__n_estimators': [100, 200],
        'classifier__max_depth': [10, 20, None],
    }
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    grid_search = GridSearchCV(model_pipeline, param_grid, cv=5, scoring='roc_auc')
    grid_search.fit(X_train, y_train)
    
    # 7. 시각화 및 검증
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    print(f"Best AUC-ROC: {grid_search.best_score_}")
    print(classification_report(y_test, y_pred))
    
    # 8. 파이프라인 저장
    joblib.dump(best_model, 'AI/GW/colon_pipeline.joblib')
    print("Model saved: AI/GW/colon_pipeline.joblib")

if __name__ == "__main__":
    train_colon_model('AI/GW/dataset/colorectal_cancer_dataset.csv')