"""Hybrid ML analysis on FULL dataset (all provinces, 2020-2026)."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('HYBRID ML ON FULL DATASET (ALL PROVINCES, 2020-2026)')
print('='*70)
print(f'Total: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_target(record):
    val = record.get('special')
    return int(str(val)[-2:]) if pd.notna(val) and val != '' else None

def create_features(records, idx):
    features = []
    # Lag features
    for lag in range(1, 8):
        if idx - lag >= 0:
            val = records[idx - lag].get('special')
            features.append(int(str(val)[-2:]) if pd.notna(val) and val != '' else 0)
        else:
            features.append(0)

    # Rolling stats
    recent = []
    for i in range(max(0, idx-10), idx):
        val = records[i].get('special')
        if pd.notna(val) and val != '':
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

def stat_predict(records, idx, window=30):
    freq = {i: 0 for i in range(100)}
    ls = {i: -1 for i in range(100)}
    start = max(0, idx - window)
    for i in range(start, idx):
        val = records[i].get('special')
        if pd.notna(val) and val != '':
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
# THOMPSON SAMPLING
# ============================================================
class ThompsonSampling:
    def __init__(self, n_arms=100):
        self.alpha = np.ones(n_arms)
        self.beta = np.ones(n_arms)

    def update(self, chosen, actual):
        for arm in chosen:
            self.alpha[arm] += 1 if arm == actual else 0
            self.beta[arm] += 0 if arm == actual else 1

    def sample(self, n=6):
        samples = np.random.beta(self.alpha, self.beta)
        return set(np.argsort(samples)[-n:])

# ============================================================
# RUN BACKTEST ON ALL PROVINCES
# ============================================================
print('Running backtest on all provinces...')
print()

prov_names = {
    'AG': 'An Giang', 'BD': 'Binh Duong', 'BL': 'Bac Lieu', 'BP': 'Binh Phuoc',
    'BTH': 'Binh Thuan', 'BTR': 'Ben Tre', 'CM': 'Ca Mau', 'CT': 'Can Tho',
    'DL': 'Da Lat', 'DNA': 'Dong Nai', 'DT': 'Dong Thap', 'HCM': 'TP.HCM',
    'HGG': 'Hau Giang', 'KG': 'Kien Giang', 'LA': 'Long An', 'ST': 'Soc Trang',
    'TGI': 'Tien Giang', 'TNI': 'Tay Ninh', 'TV': 'Tra Vinh', 'VL': 'Vinh Long',
    'VT': 'Vung Tau', 'TTP': 'TP.HCM 2'
}

all_results = {}

for prov in df['province'].unique():
    prov_data = df[df['province'] == prov].sort_values('date')
    if len(prov_data) < 100:
        continue

    prov_name = prov_names.get(prov, prov)
    records = prov_data.to_dict('records')
    targets = [get_target(r) for r in records]

    # Train XGBoost
    X_train = []
    y_train = []
    for i in range(30, len(records)):
        features = create_features(records, i)
        target = targets[i]
        if target is not None:
            X_train.append(features)
            y_train.append(target)

    if len(X_train) < 50:
        continue

    le = LabelEncoder()
    y_enc = le.fit_transform(y_train)
    X_arr = np.array(X_train, dtype=np.float32)

    xgb_model = xgb.XGBClassifier(n_estimators=50, max_depth=5, random_state=42, verbosity=0)
    xgb_model.fit(X_arr, y_enc)

    # Run backtest
    ts = ThompsonSampling()
    results = {'ts': [], 'xgb': [], 'stat': [], 'ensemble': []}

    for i in range(30, len(records)):
        actual = targets[i]
        if actual is None:
            continue

        # Thompson Sampling
        ts_pred = ts.sample(6)
        results['ts'].append(1 if actual in ts_pred else 0)

        # XGBoost
        features = create_features(records, i)
        xgb_proba = xgb_model.predict_proba(np.array([features], dtype=np.float32))[0]
        xgb_top6 = set(le.inverse_transform(np.argsort(xgb_proba)[-6:]))
        results['xgb'].append(1 if actual in xgb_top6 else 0)

        # Statistical
        stat_pred = stat_predict(records, i)
        results['stat'].append(1 if actual in stat_pred else 0)

        # Ensemble (vote)
        vote_count = Counter()
        for pred in [ts_pred, xgb_top6, stat_pred]:
            vote_count.update(pred)
        ensemble = set([n for n, c in vote_count.most_common(6)])
        results['ensemble'].append(1 if actual in ensemble else 0)

        # Update Thompson
        ts.update(ts_pred, actual)

    # Calculate accuracies
    accs = {}
    for method in ['ts', 'xgb', 'stat', 'ensemble']:
        accs[method] = np.mean(results[method]) * 100 if results[method] else 0

    all_results[prov] = accs

# ============================================================
# PRINT RESULTS TABLE
# ============================================================
print()
print('='*70)
print('RESULTS BY PROVINCE')
print('='*70)
print()

print(f'{"Tinh":<15} {"Thompson":<10} {"XGBoost":<10} {"Stat":<10} {"Ensemble":<10} {"Best":<10}')
print('-' * 65)

for prov in sorted(all_results.keys()):
    prov_name = prov_names.get(prov, prov)
    r = all_results[prov]
    best_method = max(r, key=r.get)
    best_acc = r[best_method]
    print(f'{prov_name:<15} {r["ts"]:.1f}%{" ":<4} {r["xgb"]:.1f}%{" ":<4} {r["stat"]:.1f}%{" ":<4} {r["ensemble"]:.1f}%{" ":<4} {best_method}({best_acc:.1f}%)')

print('-' * 65)

# Overall averages
print(f'{"TRUNG BINH":<15}', end='')
for method in ['ts', 'xgb', 'stat', 'ensemble']:
    avg = np.mean([r[method] for r in all_results.values()])
    print(f'{avg:.1f}%{" ":<4}', end='')
print()

# ============================================================
# ANALYSIS
# ============================================================
print()
print('='*70)
print('PHAN TICH')
print('='*70)
print()

for method, name in [('ts', 'Thompson'), ('xgb', 'XGBoost'), ('stat', 'Statistical'), ('ensemble', 'Ensemble')]:
    accs = [r[method] for r in all_results.values()]
    avg = np.mean(accs)
    better = sum(1 for a in accs if a > 6)
    print(f'{name}: TB {avg:.1f}% | {better}/{len(all_results)} tinh > 6%')

print()
print('Random baseline: 6.0%')
print()

# Best province
best_prov = max(all_results.items(), key=lambda x: max(x[1].values()))
worst_prov = min(all_results.items(), key=lambda x: max(x[1].values()))

print(f'Tinh tot nhat: {prov_names.get(best_prov[0], best_prov[0])} ({max(best_prov[1].values()):.1f}%)')
print(f'Tinh kem nhat: {prov_names.get(worst_prov[0], worst_prov[0])} ({max(worst_prov[1].values()):.1f}%)')
