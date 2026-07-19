"""XGBoost and LightGBM analysis for XSMN lottery."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import lightgbm as lgb

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*60)
print('XGBOOST & LIGHTGBM ANALYSIS FOR XSMN LOTTERY')
print('='*60)
print(f'Data: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Date range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# ============================================================
# 1. FEATURE ENGINEERING (Enhanced)
# ============================================================
print('=== 1. FEATURE ENGINEERING ===')
print()

def create_features(df_prov, target_col='special'):
    """Create comprehensive features for ML models."""
    df_prov = df_prov.sort_values('date').reset_index(drop=True)

    # Target: last 2 digits of special prize
    df_prov['target'] = df_prov[target_col].apply(lambda x: int(str(x)[-2:]) if pd.notna(x) else None)

    # Time features
    df_prov['day_of_week'] = df_prov['date'].dt.dayofweek
    df_prov['day_of_month'] = df_prov['date'].dt.day
    df_prov['month'] = df_prov['date'].dt.month
    df_prov['week_of_year'] = df_prov['date'].dt.isocalendar().week.astype(int)
    df_prov['is_weekend'] = (df_prov['day_of_week'] >= 5).astype(int)

    # Lag features (previous results)
    for lag in range(1, 15):
        df_prov[f'lag_{lag}'] = df_prov['target'].shift(lag)

    # Rolling statistics
    for window in [3, 5, 7, 10, 14, 30]:
        df_prov[f'rolling_mean_{window}'] = df_prov['target'].rolling(window).mean()
        df_prov[f'rolling_std_{window}'] = df_prov['target'].rolling(window).std()
        df_prov[f'rolling_min_{window}'] = df_prov['target'].rolling(window).min()
        df_prov[f'rolling_max_{window}'] = df_prov['target'].rolling(window).max()
        df_prov[f'rolling_median_{window}'] = df_prov['target'].rolling(window).median()

    # Frequency features
    for window in [7, 14, 30]:
        df_prov[f'freq_last_{window}'] = df_prov['target'].rolling(window).apply(
            lambda x: len(set(x.dropna().astype(int).tolist())), raw=False
        )

    # Overdue features
    df_prov['days_since_last'] = 0
    for i in range(len(df_prov)):
        if pd.notna(df_prov.loc[i, 'target']):
            val = df_prov.loc[i, 'target']
            for j in range(i-1, -1, -1):
                if df_prov.loc[j, 'target'] == val:
                    df_prov.loc[i, 'days_since_last'] = i - j
                    break

    # Pattern features
    df_prov['same_as_prev'] = (df_prov['target'] == df_prov['target'].shift(1)).astype(int)
    df_prov['diff_from_prev'] = df_prov['target'] - df_prov['target'].shift(1)

    return df_prov

# Process all provinces
all_features = []
for prov in df['province'].unique():
    df_prov = df[df['province'] == prov].copy()
    df_prov = create_features(df_prov)
    df_prov['province'] = prov
    all_features.append(df_prov)

df_all = pd.concat(all_features, ignore_index=True)
df_all = df_all.dropna()

print(f'Total records after feature engineering: {len(df_all)}')
print(f'Features created: {len(df_all.columns) - 4}')  # Exclude date, special, target, province
print()

# ============================================================
# 2. XGBOOST
# ============================================================
print('=== 2. XGBOOST ===')
print()

# Prepare features
feature_cols = [c for c in df_all.columns if c not in ['date', 'special', 'target', 'province']]
X = df_all[feature_cols].values
y = df_all['target'].values

# Time series split
tscv = TimeSeriesSplit(n_splits=5)

xgb_scores = []
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # XGBoost Classifier
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='mlogloss'
    )
    xgb_model.fit(X_train, y_train)
    y_pred = xgb_model.predict(X_test)
    score = accuracy_score(y_test, y_pred)
    xgb_scores.append(score)

print(f'XGBoost Accuracy (5-fold time series CV):')
print(f'  Mean: {np.mean(xgb_scores)*100:.2f}%')
print(f'  Std: {np.std(xgb_scores)*100:.2f}%')
print(f'  Random baseline: 1/100 = 1.00%')
print()

# Feature importance
xgb_full = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42)
xgb_full.fit(X, y)
importances = xgb_full.feature_importances_
feature_importance = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)

print('Top 15 Feature Importance (XGBoost):')
for feat, imp in feature_importance[:15]:
    print(f'  {feat}: {imp:.4f}')
print()

# ============================================================
# 3. LIGHTGBM
# ============================================================
print('=== 3. LIGHTGBM ===')
print()

lgb_scores = []
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # LightGBM Classifier
    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbose=-1
    )
    lgb_model.fit(X_train, y_train)
    y_pred = lgb_model.predict(X_test)
    score = accuracy_score(y_test, y_pred)
    lgb_scores.append(score)

print(f'LightGBM Accuracy (5-fold time series CV):')
print(f'  Mean: {np.mean(lgb_scores)*100:.2f}%')
print(f'  Std: {np.std(lgb_scores)*100:.2f}%')
print(f'  Random baseline: 1/100 = 1.00%')
print()

# Feature importance
lgb_full = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=42, verbose=-1)
lgb_full.fit(X, y)
importances_lgb = lgb_full.feature_importances_
feature_importance_lgb = sorted(zip(feature_cols, importances_lgb), key=lambda x: x[1], reverse=True)

print('Top 15 Feature Importance (LightGBM):')
for feat, imp in feature_importance_lgb[:15]:
    print(f'  {feat}: {imp}')
print()

# ============================================================
# 4. TOP-6 PREDICTION ACCURACY
# ============================================================
print('=== 4. TOP-6 PREDICTION (Special Prize) ===')
print()

# For each province, test top-6 prediction accuracy
results = {}
for prov in df['province'].unique():
    prov_data = df_all[df_all['province'] == prov].sort_values('date')
    if len(prov_data) < 100:
        continue

    test_size = int(len(prov_data) * 0.2)
    train_end = len(prov_data) - test_size

    X_prov = prov_data[feature_cols].values
    y_prov = prov_data['target'].values

    X_train = X_prov[:train_end]
    y_train = y_prov[:train_end]
    X_test = X_prov[train_end:]
    y_test = y_prov[train_end:]

    # Train XGBoost with LabelEncoder
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)

    model = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42, verbose=0)
    model.fit(X_train, y_train_encoded)

    # Get probability predictions
    y_proba = model.predict_proba(X_test)

    # For each test sample, get top 6 predicted numbers
    correct = 0
    total = 0
    for i in range(len(y_proba)):
        # Get top 6 class indices
        top6_indices = np.argsort(y_proba[i])[-6:]
        # Convert back to original labels
        top6_labels = set(le.inverse_transform(top6_indices))
        actual = int(y_test[i])
        total += 1
        if actual in top6_labels:
            correct += 1

    acc = correct / total * 100 if total > 0 else 0
    results[prov] = acc

prov_names = {
    'AG': 'An Giang', 'BD': 'Binh Duong', 'BL': 'Bac Lieu', 'BP': 'Binh Phuoc',
    'BTH': 'Binh Thuan', 'BTR': 'Ben Tre', 'CM': 'Ca Mau', 'CT': 'Can Tho',
    'DL': 'Da Lat', 'DNA': 'Dong Nai', 'DT': 'Dong Thap', 'HCM': 'TP.HCM',
    'HGG': 'Hau Giang', 'KG': 'Kien Giang', 'LA': 'Long An', 'ST': 'Soc Trang',
    'TGI': 'Tien Giang', 'TNI': 'Tay Ninh', 'TV': 'Tra Vinh', 'VL': 'Vinh Long',
    'VT': 'Vung Tau', 'TTP': 'TP.HCM 2'
}

print(f'{"Tinh":<15} {"Accuracy":<12} {"vs Random (6%)"}')
print('-' * 45)
for prov in sorted(results.keys()):
    prov_name = prov_names.get(prov, prov)
    acc = results[prov]
    marker = '+' if acc > 6 else '-'
    print(f'{prov_name:<15} {acc:.1f}%{" ":<6} {marker}')

avg = np.mean(list(results.values()))
print('-' * 45)
print(f'{"Trung binh":<15} {avg:.1f}%{" ":<6} {"+" if avg > 6 else "-"}')
print()

# ============================================================
# 5. CONCLUSION
# ============================================================
print('=== 5. KET LUAN ===')
print()
print('Mo hinh:')
print(f'  XGBoost:   {np.mean(xgb_scores)*100:.2f}% (random: 1.00%)')
print(f'  LightGBM:  {np.mean(lgb_scores)*100:.2f}% (random: 1.00%)')
print()
print('Top-6 Prediction (Special Prize):')
print(f'  Trung binh: {avg:.1f}% (random: 6.0%)')
print()

if avg > 7:
    print('Ket luan: XGBoost CO EDGE nho so voi ngau nhien')
else:
    print('Ket luan: XGBoost KHONG CO EDGE ro rang')
    print('Xo so that su ngau nhien')
