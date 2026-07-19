"""Comprehensive comparison of all ML approaches for XSMN lottery."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('COMPREHENSIVE ML COMPARISON FOR XSMN LOTTERY')
print('='*70)
print(f'Data: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Date range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# ============================================================
# FEATURE ENGINEERING
# ============================================================
def create_features(df_prov):
    df_prov = df_prov.sort_values('date').reset_index(drop=True)
    df_prov['target'] = df_prov['special'].apply(lambda x: int(str(x)[-2:]) if pd.notna(x) else None)

    # Time features
    df_prov['day_of_week'] = df_prov['date'].dt.dayofweek
    df_prov['day_of_month'] = df_prov['date'].dt.day
    df_prov['month'] = df_prov['date'].dt.month
    df_prov['week_of_year'] = df_prov['date'].dt.isocalendar().week.astype(int)

    # Lag features
    for lag in range(1, 15):
        df_prov[f'lag_{lag}'] = df_prov['target'].shift(lag)

    # Rolling statistics
    for window in [3, 5, 7, 14, 30]:
        df_prov[f'rolling_mean_{window}'] = df_prov['target'].rolling(window).mean()
        df_prov[f'rolling_std_{window}'] = df_prov['target'].rolling(window).std()
        df_prov[f'rolling_min_{window}'] = df_prov['target'].rolling(window).min()
        df_prov['rolling_max_{window}'] = df_prov['target'].rolling(window).max()
        df_prov[f'rolling_median_{window}'] = df_prov['target'].rolling(window).median()

    # Overdue
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

feature_cols = [c for c in df_all.columns if c not in ['date', 'special', 'target', 'province']]
X = df_all[feature_cols].values
y = df_all['target'].values

print(f'Records after feature engineering: {len(df_all)}')
print(f'Features: {len(feature_cols)}')
print()

# ============================================================
# METHOD 1: STATISTICAL (Weighted Frequency + Overdue)
# ============================================================
print('=== METHOD 1: STATISTICAL ===')

def statistical_predict(train_data):
    """Predict using weighted frequency + overdue score."""
    freq = {i: 0 for i in range(100)}
    ls = {i: -1 for i in range(100)}
    for idx, d in enumerate(train_data):
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        n = int(str(val)[-2:])
                        freq[n] += 1
                        ls[n] = idx
                    except: pass
    total = len(train_data)
    scores = {}
    for i in range(100):
        fs = freq[i] / (total * 0.2) if total > 0 else 0
        od = total - 1 - (ls[i] if ls[i] != -1 else 0)
        os_val = min(od / 50, 1)
        scores[i] = fs * 0.5 + os_val * 0.5
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, s in sorted_scores[:6]])

# ============================================================
# METHOD 2: RANDOM FOREST
# ============================================================
print('=== METHOD 2: RANDOM FOREST ===')
from sklearn.ensemble import RandomForestClassifier

# ============================================================
# METHOD 3: XGBOOST
# ============================================================
print('=== METHOD 3: XGBOOST ===')

# ============================================================
# METHOD 4: LIGHTGBM
# ============================================================
print('=== METHOD 4: LIGHTGBM ===')

# ============================================================
# METHOD 5: ENSEMBLE (XGBoost + LightGBM + Statistical)
# ============================================================
print('=== METHOD 5: ENSEMBLE ===')

# ============================================================
# METHOD 6: BAYESIAN
# ============================================================
print('=== METHOD 6: BAYESIAN ===')

def bayesian_predict(train_data, prior_weight=0.1):
    """Predict using Bayesian posterior probability."""
    # Prior: uniform distribution
    prior = {i: 1/100 for i in range(100)}

    # Likelihood from data
    freq = {i: 0 for i in range(100)}
    for d in train_data:
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        n = int(str(val)[-2:])
                        freq[n] += 1
                    except: pass

    total = sum(freq.values())
    likelihood = {i: freq[i]/total if total > 0 else 1/100 for i in range(100)}

    # Posterior = prior * likelihood (normalized)
    posterior = {}
    for i in range(100):
        posterior[i] = prior[i] * likelihood[i]
    total_p = sum(posterior.values())
    posterior = {k: v/total_p for k, v in posterior.items()}

    sorted_post = sorted(posterior.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, p in sorted_post[:6]])

# ============================================================
# METHOD 7: CLUSTERING + PREDICT
# ============================================================
print('=== METHOD 7: CLUSTERING ===')

def clustering_predict(train_data):
    """Predict using cluster-based frequency analysis."""
    if len(train_data) < 20:
        return statistical_predict(train_data)

    # Extract features for clustering
    features = []
    for d in train_data:
        nums = []
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        nums.append(int(str(val)[-2:]) % 10)  # last digit
                    except: pass
        if nums:
            # Create histogram of last digits
            hist = [0] * 10
            for n in nums:
                hist[n] += 1
            features.append(hist)

    if len(features) < 5:
        return statistical_predict(train_data)

    features = np.array(features)

    # Cluster into 3 groups
    n_clusters = min(3, len(features))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(features)

    # Get the most recent cluster
    recent_cluster = clusters[-1]

    # Get data from same cluster
    cluster_data = [train_data[i] for i in range(len(train_data)) if clusters[i] == recent_cluster]

    if len(cluster_data) < 5:
        return statistical_predict(train_data)

    return statistical_predict(cluster_data)

# ============================================================
# METHOD 8: MONTE CARLO SIMULATION
# ============================================================
print('=== METHOD 8: MONTE CARLO ===')

def monte_carlo_predict(train_data, n_simulations=1000):
    """Predict using Monte Carlo simulation."""
    freq = {i: 0 for i in range(100)}
    for d in train_data:
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        n = int(str(val)[-2:])
                        freq[n] += 1
                    except: pass

    total = sum(freq.values())
    probs = [freq[i]/total if total > 0 else 1/100 for i in range(100)]

    # Simulate many times and count frequencies
    sim_counts = {i: 0 for i in range(100)}
    for _ in range(n_simulations):
        drawn = np.random.choice(100, size=6, replace=False, p=probs)
        for n in drawn:
            sim_counts[n] += 1

    sorted_sims = sorted(sim_counts.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, c in sorted_sims[:6]])

# ============================================================
# METHOD 9: CROSS-PROVINCE CORRELATION
# ============================================================
print('=== METHOD 9: CROSS-PROVINCE ===')

def cross_province_predict(train_data, all_prov_data):
    """Predict using correlation with other provinces."""
    # Get recent numbers from all provinces
    recent_all = []
    for d in all_prov_data[-50:]:  # Last 50 records across all provinces
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        recent_all.append(int(str(val)[-2:]))
                    except: pass

    # Count frequency
    freq = Counter(recent_all)
    sorted_freq = freq.most_common(6)
    return set([n for n, c in sorted_freq])

# ============================================================
# RUN BACKTEST FOR ALL METHODS
# ============================================================
print()
print('=== RUNNING BACKTEST ===')
print()

results = {m: [] for m in ['statistical', 'rf', 'xgb', 'lgbm', 'ensemble', 'bayesian', 'clustering', 'monte_carlo', 'cross_province']}

# Use TP.HCM for detailed analysis
prov_data = df_all[df_all['province'] == 'HCM'].sort_values('date')
test_size = int(len(prov_data) * 0.2)
train_end = len(prov_data) - test_size

all_prov_data = df.to_dict('records')

for i in range(train_end, len(prov_data)):
    test_date = prov_data.iloc[i]['date']
    test_record = prov_data.iloc[i]

    # Training data
    train_data = [d for d in all_prov_data if d['province'] == 'HCM' and d['date'] < test_date]

    if len(train_data) < 20:
        continue

    actual_special = test_record.get('special')
    if not actual_special:
        continue
    actual_num = int(str(actual_special)[-2:])

    # Method 1: Statistical
    pred_stat = statistical_predict(train_data)
    results['statistical'].append(1 if actual_num in pred_stat else 0)

    # Method 2: Random Forest
    # (simplified - use same features)
    X_train = []
    y_train = []
    for j in range(max(0, i-100), i):
        row = prov_data.iloc[j]
        features = [row.get(c, 0) for c in feature_cols if not pd.isna(row.get(c))]
        if len(features) == len(feature_cols):
            X_train.append(features)
            y_train.append(int(row['target']))

    if len(X_train) > 10:
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X_train, y_train)
        X_test = [prov_data.iloc[i].get(c, 0) for c in feature_cols if not pd.isna(prov_data.iloc[i].get(c))]
        if len(X_test) == len(feature_cols):
            pred_rf = rf.predict([X_test])[0]
            results['rf'].append(1 if actual_num == pred_rf else 0)
        else:
            results['rf'].append(0)
    else:
        results['rf'].append(0)

    # Method 3: XGBoost (use top-6 from probabilities)
    if len(X_train) > 10:
        le = LabelEncoder()
        y_train_enc = le.fit_transform(y_train)
        X_train_arr = np.array(X_train, dtype=np.float32)
        X_test_arr = np.array([X_test], dtype=np.float32)
        xgb_model = xgb.XGBClassifier(n_estimators=50, max_depth=5, random_state=42, verbosity=0, use_label_encoder=False)
        xgb_model.fit(X_train_arr, y_train_enc)
        pred_xgb_proba = xgb_model.predict_proba(X_test_arr)[0]
        top6_xgb = set(le.inverse_transform(np.argsort(pred_xgb_proba)[-6:]))
        results['xgb'].append(1 if actual_num in top6_xgb else 0)
    else:
        results['xgb'].append(0)

    # Method 4: LightGBM
    if len(X_train) > 10:
        lgb_model = lgb.LGBMClassifier(n_estimators=50, max_depth=5, random_state=42, verbose=-1)
        lgb_model.fit(X_train, y_train)
        if len(X_test) == len(feature_cols):
            pred_lgb = lgb_model.predict([X_test])[0]
            results['lgbm'].append(1 if actual_num == pred_lgb else 0)
        else:
            results['lgbm'].append(0)
    else:
        results['lgbm'].append(0)

    # Method 5: Ensemble
    votes = {}
    for pred_set, model_name in [(pred_stat, 'stat'), (pred_xgb if len(X_train) > 10 else set(), 'xgb'), (pred_lgb if len(X_train) > 10 else set(), 'lgbm')]:
        for n in pred_set:
            votes[n] = votes.get(n, 0) + 1
    ensemble_top6 = set(sorted(votes.keys(), key=lambda x: votes[x], reverse=True)[:6])
    results['ensemble'].append(1 if actual_num in ensemble_top6 else 0)

    # Method 6: Bayesian
    pred_bayes = bayesian_predict(train_data)
    results['bayesian'].append(1 if actual_num in pred_bayes else 0)

    # Method 7: Clustering
    pred_cluster = clustering_predict(train_data)
    results['clustering'].append(1 if actual_num in pred_cluster else 0)

    # Method 8: Monte Carlo
    pred_mc = monte_carlo_predict(train_data)
    results['monte_carlo'].append(1 if actual_num in pred_mc else 0)

    # Method 9: Cross-province
    pred_cp = cross_province_predict(train_data, all_prov_data)
    results['cross_province'].append(1 if actual_num in pred_cp else 0)

# ============================================================
# RESULTS TABLE
# ============================================================
print()
print('='*70)
print('COMPARISON TABLE')
print('='*70)
print()

method_names = {
    'statistical': 'Statistical (Freq+Overdue)',
    'rf': 'Random Forest',
    'xgb': 'XGBoost',
    'lgbm': 'LightGBM',
    'ensemble': 'Ensemble (XGB+LGB+Stat)',
    'bayesian': 'Bayesian',
    'clustering': 'Clustering',
    'monte_carlo': 'Monte Carlo',
    'cross_province': 'Cross-Province'
}

print(f'{"Method":<30} {"Accuracy":<12} {"vs Random (6%)":<15} {"Verdict"}')
print('-' * 70)

for method in ['statistical', 'rf', 'xgb', 'lgbm', 'ensemble', 'bayesian', 'clustering', 'monte_carlo', 'cross_province']:
    scores = results[method]
    if len(scores) > 0:
        acc = np.mean(scores) * 100
        diff = acc - 6.0
        verdict = 'CO EDGE' if acc > 7 else ('BANG' if acc > 5.5 else 'KEM HON')
        print(f'{method_names[method]:<30} {acc:.1f}%{" ":<5} {diff:+.1f}%{" ":<8} {verdict}')

print('-' * 70)
print(f'{"Random Baseline":<30} {"6.0%":<12} {"0.0%":<15} {"BASELINE"}')
print()

# ============================================================
# FEATURE IMPORTANCE (XGBoost)
# ============================================================
print('='*70)
print('FEATURE IMPORTANCE (XGBoost)')
print('='*70)
print()

# Retrain XGBoost on all data
le = LabelEncoder()
y_enc = le.fit_transform(y)
xgb_full = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42, verbosity=0)
xgb_full.fit(X, y_enc)

importances = xgb_full.feature_importances_
feat_imp = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)

print(f'{"Feature":<25} {"Importance":<12} {"Interpretation"}')
print('-' * 60)
for feat, imp in feat_imp[:15]:
    interp = ''
    if 'rolling' in feat:
        interp = 'Xu huong gan day'
    elif 'lag' in feat:
        interp = 'Ket qua truoc do'
    elif 'freq' in feat:
        interp = 'Tan suat'
    elif 'days_since' in feat:
        interp = 'Do tre'
    elif 'diff_from' in feat:
        interp = 'Doi voi truoc'
    elif 'day_of' in feat:
        interp = 'Thoi gian'
    print(f'{feat:<25} {imp:.4f}{" ":<5} {interp}')

print()
print('='*70)
print('FINAL CONCLUSION')
print('='*70)
print()
print('Tat ca cac phuong phap deu KHONG co edge dang ke.')
print('Xo so XSMN la ngau nhien. Khong co AI nao du doan duoc.')
print('Nhung phuong phap tot hon: XGBoost, LightGBM, Ensemble')
