"""Hybrid ML: Thompson Sampling + XGBoost + Ensemble."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import lightgbm as lgb
import random
import warnings
warnings.filterwarnings('ignore')

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('HYBRID ML: THOMPSON + XGBOOST + ENSEMBLE')
print('='*70)
print(f'Data: {len(df)} records')
print()

# Use TP.HCM
hcm_data = df[df['province'] == 'HCM'].sort_values('date')
print(f'TP.HCM: {len(hcm_data)} records')
print()

# Extract targets
targets = []
records_list = hcm_data.to_dict('records')
for r in records_list:
    val = r.get('special')
    targets.append(int(str(val)[-2:]) if pd.notna(val) else 0)

# ============================================================
# MODEL 1: THOMPSON SAMPLING
# ============================================================
class ThompsonSampling:
    def __init__(self, n_arms=100, alpha=1.0, beta=1.0):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms) * alpha
        self.beta = np.ones(n_arms) * beta

    def update(self, chosen, actual):
        for arm in chosen:
            self.alpha[arm] += 1 if arm == actual else 0
            self.beta[arm] += 0 if arm == actual else 1

    def sample(self, n=6):
        samples = np.random.beta(self.alpha, self.beta)
        return set(np.argsort(samples)[-n:])

    def get_top6(self):
        return set(np.argsort(self.alpha / (self.alpha + self.beta))[-6:])

# ============================================================
# MODEL 2: XGBOOST
# ============================================================
def create_xgboost_features(records, idx):
    """Create features for XGBoost prediction."""
    features = []

    # Lag features (last 7 numbers)
    for lag in range(1, 8):
        if idx - lag >= 0:
            val = records[idx - lag].get('special')
            if pd.notna(val):
                features.append(int(str(val)[-2:]))
            else:
                features.append(0)
        else:
            features.append(0)

    # Rolling mean/std of last 10
    recent = []
    for i in range(max(0, idx-10), idx):
        val = records[i].get('special')
        if pd.notna(val):
            recent.append(int(str(val)[-2:]))
    features.append(np.mean(recent) if recent else 0)
    features.append(np.std(recent) if len(recent) > 1 else 0)
    features.append(min(recent) if recent else 0)
    features.append(max(recent) if recent else 0)

    # Time features
    date = records[idx]['date']
    features.append(date.dayofweek)
    features.append(date.day)
    features.append(date.month)

    return features

# ============================================================
# MODEL 3: FREQUENCY + OVERDUE
# ============================================================
def stat_predict(records, idx, window=30):
    """Statistical prediction based on frequency + overdue."""
    freq = {i: 0 for i in range(100)}
    ls = {i: -1 for i in range(100)}

    start = max(0, idx - window)
    for i in range(start, idx):
        val = records[i].get('special')
        if pd.notna(val):
            n = int(str(val)[-2:])
            freq[n] += 1
            ls[n] = i

    total = idx - start
    scores = {}
    for i in range(100):
        fs = freq[i] / (total * 0.2) if total > 0 else 0
        od = idx - 1 - (ls[i] if ls[i] != -1 else 0)
        os_val = min(od / 50, 1)
        scores[i] = fs * 0.5 + os_val * 0.5

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, s in sorted_scores[:6]])

# ============================================================
# TRAIN XGBOOST
# ============================================================
print('Training XGBoost...')

X_train_xgb = []
y_train_xgb = []

for i in range(30, len(records_list)):
    features = create_xgboost_features(records_list, i)
    target = targets[i]
    X_train_xgb.append(features)
    y_train_xgb.append(target)

X_train_xgb = np.array(X_train_xgb, dtype=np.float32)
y_train_xgb = np.array(y_train_xgb)

le = LabelEncoder()
y_train_enc = le.fit_transform(y_train_xgb)

xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    verbosity=0
)
xgb_model.fit(X_train_xgb, y_train_enc)
print('XGBoost trained!')
print()

# ============================================================
# RUN BACKTEST WITH HYBRID APPROACHES
# ============================================================
print('Running backtest...')
print()

results = {
    'Thompson': [],
    'XGBoost': [],
    'Statistical': [],
    'Ensemble_Vote': [],
    'Ensemble_Weighted': [],
    'Hybrid_TS_XGB': [],
}

ts = ThompsonSampling()

for i in range(30, len(records_list)):
    actual = targets[i]

    # Thompson Sampling prediction
    ts_pred = ts.sample(6)
    results['Thompson'].append(1 if actual in ts_pred else 0)

    # XGBoost prediction
    features = create_xgboost_features(records_list, i)
    features_arr = np.array([features], dtype=np.float32)
    xgb_proba = xgb_model.predict_proba(features_arr)[0]
    xgb_top6 = set(le.inverse_transform(np.argsort(xgb_proba)[-6:]))
    results['XGBoost'].append(1 if actual in xgb_top6 else 0)

    # Statistical prediction
    stat_pred = stat_predict(records_list, i)
    results['Statistical'].append(1 if actual in stat_pred else 0)

    # Ensemble Vote (majority vote)
    all_preds = [ts_pred, xgb_top6, stat_pred]
    vote_count = Counter()
    for pred in all_preds:
        vote_count.update(pred)
    ensemble_vote = set([n for n, c in vote_count.most_common(6)])
    results['Ensemble_Vote'].append(1 if actual in ensemble_vote else 0)

    # Ensemble Weighted (TS 40%, XGB 35%, Stat 25%)
    scores = defaultdict(float)
    for n in ts_pred:
        scores[n] += 0.40
    for n in xgb_top6:
        scores[n] += 0.35
    for n in stat_pred:
        scores[n] += 0.25
    ensemble_weighted = set(sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:6])
    results['Ensemble_Weighted'].append(1 if actual in ensemble_weighted else 0)

    # Hybrid: Use TS to filter XGB predictions
    # XGB predicts top 20, TS filters to top 6
    xgb_top20 = set(le.inverse_transform(np.argsort(xgb_proba)[-20:]))
    ts_scores = {}
    for n in xgb_top20:
        ts_scores[n] = ts.alpha[n] / (ts.alpha[n] + ts.beta[n])
    hybrid_ts_xgb = set(sorted(ts_scores.keys(), key=lambda x: ts_scores[x], reverse=True)[:6])
    results['Hybrid_TS_XGB'].append(1 if actual in hybrid_ts_xgb else 0)

    # Update Thompson Sampling
    ts.update(ts_pred, actual)

# ============================================================
# RESULTS
# ============================================================
print()
print('='*70)
print('RESULTS COMPARISON')
print('='*70)
print()

print(f'{"Method":<25} {"Accuracy":<12} {"vs Random (6%)":<15} {"Verdict"}')
print('-' * 65)

for name in ['Thompson', 'XGBoost', 'Statistical', 'Ensemble_Vote', 'Ensemble_Weighted', 'Hybrid_TS_XGB']:
    scores = results[name]
    acc = np.mean(scores) * 100 if len(scores) > 0 else 0
    diff = acc - 6.0
    verdict = 'CO EDGE' if acc > 7 else ('BANG' if acc > 5.5 else 'KEM HON')
    print(f'{name:<25} {acc:.2f}%{" ":<5} {diff:+.2f}%{" ":<8} {verdict}')

print('-' * 65)
print(f'{"Random":<25} {"6.00%":<12} {"0.00%":<15} {"BASELINE"}')
print()

# ============================================================
# FIND BEST COMBINATION
# ============================================================
print('='*70)
print('BEST COMBINATION ANALYSIS')
print('='*70)
print()

# Try different weight combinations
best_acc = 0
best_weights = None

for w1 in np.arange(0.1, 0.7, 0.1):  # Thompson weight
    for w2 in np.arange(0.1, 0.7, 0.1):  # XGBoost weight
        w3 = 1 - w1 - w2
        if w3 < 0:
            continue

        combo_scores = []
        for i in range(30, len(records_list)):
            actual = targets[i]

            # Get predictions from each model
            ts_pred = ts.sample(6)  # Use final TS state
            features = create_xgboost_features(records_list, i)
            xgb_proba = xgb_model.predict_proba(np.array([features], dtype=np.float32))[0]
            xgb_top6 = set(le.inverse_transform(np.argsort(xgb_proba)[-6:]))
            stat_pred = stat_predict(records_list, i)

            # Weighted combination
            scores = defaultdict(float)
            for n in ts_pred:
                scores[n] += w1
            for n in xgb_top6:
                scores[n] += w2
            for n in stat_pred:
                scores[n] += w3

            top6 = set(sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:6])
            combo_scores.append(1 if actual in top6 else 0)

        acc = np.mean(combo_scores) * 100
        if acc > best_acc:
            best_acc = acc
            best_weights = (w1, w2, w3)

print(f'Best weight combination:')
print(f'  Thompson: {best_weights[0]:.1f}')
print(f'  XGBoost:  {best_weights[1]:.1f}')
print(f'  Statistical: {best_weights[2]:.1f}')
print(f'  Accuracy: {best_acc:.2f}%')
print(f'  vs Random: {best_acc - 6.0:+.2f}%')
print()

# ============================================================
# FINAL CONCLUSION
# ============================================================
print('='*70)
print('KET LUAN')
print('='*70)
print()

# Find best method
all_accs = {}
for name in ['Thompson', 'XGBoost', 'Statistical', 'Ensemble_Vote', 'Ensemble_Weighted', 'Hybrid_TS_XGB']:
    all_accs[name] = np.mean(results[name]) * 100
all_accs['Best_Weighted'] = best_acc

best_method = max(all_accs.items(), key=lambda x: x[1])
print(f'Phuong phap tot nhat: {best_method[0]} ({best_method[1]:.2f}%)')
print()

if best_method[1] > 7:
    print(f'Ket luan: Co EDGE nho ({best_method[1]:.2f}% vs 6.00% random)')
    print('Nhung van KHONG du de thang xo so ve lau dai')
else:
    print('Ket luan: KHONG co phuong phap nao co EDGE ro rang')
    print('Xo so la ngau nhien - khong co AI nao du doan duoc')
