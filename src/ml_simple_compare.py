"""Simple comparison of key ML methods."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

# Load data
data = json.loads(Path('data/xsmn.json').read_text())

print('='*70)
print('ML COMPARISON FOR XSMN LOTTERY')
print('='*70)
print(f'Data: {len(data)} records')
print()

# Use TP.HCM for analysis
hcm_data = [d for d in data if d['province'] == 'HCM']
hcm_data.sort(key=lambda x: x['date'])

print(f'TP.HCM: {len(hcm_data)} records')
print()

# ============================================================
# METHOD 1: STATISTICAL (Weighted Frequency + Overdue)
# ============================================================
def statistical_predict(train_data):
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
# METHOD 2: FREQUENCY ONLY
# ============================================================
def frequency_predict(train_data):
    freq = Counter()
    for d in train_data:
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        freq[int(str(val)[-2:])] += 1
                    except: pass
    return set([n for n, c in freq.most_common(6)])

# ============================================================
# METHOD 3: OVERDUE ONLY
# ============================================================
def overdue_predict(train_data):
    ls = {i: -1 for i in range(100)}
    for idx, d in enumerate(train_data):
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        ls[int(str(val)[-2:])] = idx
                    except: pass
    total = len(train_data)
    overdue = [(n, total-1-(ls[n] if ls[n]!=-1 else 0)) for n in range(100)]
    overdue.sort(key=lambda x: x[1], reverse=True)
    return set([n for n, d in overdue[:6]])

# ============================================================
# METHOD 4: BAYESIAN
# ============================================================
def bayesian_predict(train_data):
    freq = Counter()
    for d in train_data:
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        freq[int(str(val)[-2:])] += 1
                    except: pass
    total = sum(freq.values())
    probs = {i: (freq[i]+1)/(total+100) for i in range(100)}  # Laplace smoothing
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, p in sorted_probs[:6]])

# ============================================================
# METHOD 5: RANDOM
# ============================================================
def random_predict():
    return set(np.random.choice(100, 6, replace=False))

# ============================================================
# METHOD 6: ENSEMBLE (Top 6 from all methods combined)
# ============================================================
def ensemble_predict(train_data):
    votes = Counter()
    for pred in [statistical_predict(train_data), frequency_predict(train_data),
                 overdue_predict(train_data), bayesian_predict(train_data)]:
        votes.update(pred)
    return set([n for n, c in votes.most_common(6)])

# ============================================================
# RUN BACKTEST
# ============================================================
print('=== BACKTEST RESULTS ===')
print()
print('Method                      Accuracy    vs Random (6%)')
print('-' * 55)

methods = {
    'Statistical (Freq+Overdue)': statistical_predict,
    'Frequency Only': frequency_predict,
    'Overdue Only': overdue_predict,
    'Bayesian': bayesian_predict,
    'Ensemble (All)': ensemble_predict,
}

results = {}
for name, func in methods.items():
    correct = 0
    total = 0

    for i in range(100, len(hcm_data)):
        train_data = hcm_data[:i]
        test_record = hcm_data[i]

        predicted = func(train_data)

        actual_special = test_record.get('special')
        if not actual_special:
            continue
        actual_num = int(str(actual_special)[-2:])

        total += 1
        if actual_num in predicted:
            correct += 1

    acc = correct / total * 100 if total > 0 else 0
    results[name] = acc
    diff = acc - 6.0
    marker = '+' if acc > 6 else '-'
    print(f'{name:<30} {acc:.1f}%{" ":<5} {diff:+.1f}% {marker}')

# Random baseline
print(f'{"Random":<30} {"6.0%":<12} {"0.0%":<8} =')

print()
print('='*70)
print('PHAN TICH')
print('='*70)
print()

# Find best method
best_method = max(results, key=results.get)
worst_method = min(results, key=results.get)

print(f'Phuong phap tot nhat: {best_method} ({results[best_method]:.1f}%)')
print(f'Phuong phap kem nhat: {worst_method} ({results[worst_method]:.1f}%)')
print()

if results[best_method] > 7:
    print('Ket luan: Co the co EDGE nho tu {best_method}')
else:
    print('Ket luan: KHONG co phuong phap nao co EDGE ro rang')
    print('Tat ca deu ~ 6% (ngau nhien)')

print()
print('='*70)
print('TOP 6 PREDICTION EXAMPLE (Ky gan nhat)')
print('='*70)
print()

# Show predictions for the latest draw
latest = hcm_data[-1]
print(f'Ngay: {latest["date"]}')
print(f'GDB: {latest["special"]}')
print()

# Get training data
train = hcm_data[:-1]

print('Du doan tu cac phuong phap:')
for name, func in methods.items():
    pred = func(train)
    actual = int(str(latest['special'])[-2:])
    hit = actual in pred
    print(f'  {name}: {sorted(pred)} {"TRUNG" if hit else "SAI"}')
