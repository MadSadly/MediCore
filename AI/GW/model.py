import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

# 1. 로드 및 전처리
df = pd.read_csv('AI/GW/dataset/colorectal_cancer_dataset.csv')
X = df[['Age', 'Tumor_Size_mm', 'Gender', 'Cancer_Stage', 'Obesity_BMI', 'Diabetes', 'Inflammatory_Bowel_Disease', 'Genetic_Mutation']]
y = df['Survival_Prediction'].apply(lambda x: 1 if x == 'Yes' else 0)

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), ['Age', 'Tumor_Size_mm']),
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['Gender', 'Cancer_Stage', 'Obesity_BMI', 'Diabetes', 'Inflammatory_Bowel_Disease', 'Genetic_Mutation'])
])

# 2. SMOTE (불균형 해소)
X_processed = preprocessor.fit_transform(X)
X_res, y_res = SMOTE(random_state=42).fit_resample(X_processed, y)

# 3. 모델 비교 및 최적화 (XGBoost 선정)
xgb_pipe = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', XGBClassifier(random_state=42, eval_metric='logloss'))
])

# 하이퍼파라미터 튜닝
param_grid = {'classifier__n_estimators': [100, 200], 'classifier__learning_rate': [0.01, 0.1]}
grid = GridSearchCV(xgb_pipe, param_grid, cv=3, scoring='roc_auc')
grid.fit(X, y)

# 4. 최적 모델 저장
joblib.dump(grid.best_estimator_, 'AI/GW/colon_pipeline.pkl')
