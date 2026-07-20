"""Compare Simple Voting vs Weighted Scoring Ensemble."""
import json
import numpy as np
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

# Get TP.HCM data
hcm_data = [d for d in data if d['province'] == 'HCM']
hcm_data.sort(key=lambda x: x['date'])

print('='*70)
print('ENSEMBLE COMPARISON: Simple Voting vs Weighted Scoring')
print('='*70)
print(f'TP.HCM: {len(hcm_data)} records')
print()

def calc_scores(records):
    freq = {i: 0 for i in range(100)}
    ls = {i: -1 for i in range(100)}
    for idx, d in enumerate(records):
        for k in d:
            if k.startswith('prize') or k == 'special':
                val = d[k]
                if val is not None and val != '' and val != 0:
                    try:
                        n = int(str(val)[-2:])
                        freq[n] += 1
                        ls[n] = idx
                    except: pass
    total = len(records)
    scores = {}
    for i in range(100):
        fs = freq[i] / (total * 0.2) if total > 0 else 0
        od = total - 1 - (ls[i] if ls[i] != -1 else 0)
        os_val = min(od / 50, 1)
        scores[i] = fs * 0.5 + os_val * 0.5
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores

def thompson_predict(records):
    alpha = [1] * 100
    for d in records:
        for k in d:
            if (k.startswith('prize') or k == 'special') and d[k]:
                try:
                    n = int(str(d[k])[-2:])
                    alpha[n] += 1
                except: pass
    probs = [(i, alpha[i] / (alpha[i] + 1)) for i in range(100)]
    probs.sort(key=lambda x: x[1], reverse=True)
    return set([n for n, p in probs[:6]])

def ensemble_simple_voting(records):
    """Old method: simple voting"""
    stat = set([n for n, s in calc_scores(records)[:6]])
    thompson = thompson_predict(records)
    votes = {}
    for n in stat: votes[n] = votes.get(n, 0) + 1
    for n in thompson: votes[n] = votes.get(n, 0) + 1
    return set(sorted(votes.keys(), key=lambda x: votes[x], reverse=True)[:6])

def ensemble_weighted(records):
    """New method: weighted scoring"""
    stat_sorted = calc_scores(records)
    alpha = [1] * 100
    for d in records:
        for k in d:
            if (k.startswith('prize') or k == 'special') and d[k]:
                try:
                    n = int(str(d[k])[-2:])
                    alpha[n] += 1
                except: pass

    scores = {}
    for i in range(100):
        scores[i] = 0

    # Thompson 40%
    for i in range(100):
        scores[i] += (alpha[i] / (alpha[i] + 1)) * 0.4

    # Statistical 60%
    for idx, (n, s) in enumerate(stat_sorted):
        scores[n] += (1 - idx/len(stat_sorted)) * 0.6

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, s in sorted_scores[:6]])

def stat_predict(records):
    sorted_scores = calc_scores(records)
    return set([n for n, s in sorted_scores[:6]])

def thompson_predict_set(records):
    alpha = [1] * 100
    for d in records:
        for k in d:
            if (k.startswith('prize') or k == 'special') and d[k]:
                try:
                    n = int(str(d[k])[-2:])
                    alpha[n] += 1
                except: pass
    probs = [(i, alpha[i] / (alpha[i] + 1)) for i in range(100)]
    probs.sort(key=lambda x: x[1], reverse=True)
    return set([n for n, p in probs[:6]])

# Run backtest
print('Running backtest...')
print()

results = {
    'Statistical': [],
    'Thompson': [],
    'Ensemble_Simple': [],
    'Ensemble_Weighted': [],
}

for i in range(50, len(hcm_data)):
    train_data = hcm_data[:i]
    actual = hcm_data[i].get('special')
    if not actual: continue
    actual_num = int(str(actual)[-2:])

    # Statistical
    pred_stat = stat_predict(train_data)
    results['Statistical'].append(1 if actual_num in pred_stat else 0)

    # Thompson
    pred_thompson = thompson_predict_set(train_data)
    results['Thompson'].append(1 if actual_num in pred_thompson else 0)

    # Ensemble Simple
    pred_simple = ensemble_simple_voting(train_data)
    results['Ensemble_Simple'].append(1 if actual_num in pred_simple else 0)

    # Ensemble Weighted
    pred_weighted = ensemble_weighted(train_data)
    results['Ensemble_Weighted'].append(1 if actual_num in pred_weighted else 0)

# Print results
print('='*70)
print('RESULTS COMPARISON')
print('='*70)
print()
print(f'{"Method":<25} {"Accuracy":<12} {"vs Random (6%)":<15} {"Verdict"}')
print('-' * 65)

for method in ['Statistical', 'Thompson', 'Ensemble_Simple', 'Ensemble_Weighted']:
    acc = np.mean(results[method]) * 100
    diff = acc - 6.0
    verdict = 'CO EDGE' if acc > 7 else ('BANG' if acc > 5.5 else 'KEM HON')
    print(f'{method:<25} {acc:.2f}%{" ":<5} {diff:+.2f}%{" ":<8} {verdict}')

print('-' * 65)
print(f'{"Random":<25} {"6.00%":<12} {"0.00%":<15} {"BASELINE"}')
print()

# Detailed comparison
print('='*70)
print('DETAILED COMPARISON')
print('='*70)
print()

simple_acc = np.mean(results['Ensemble_Simple']) * 100
weighted_acc = np.mean(results['Ensemble_Weighted']) * 100

print(f'Ensemble Simple Voting: {simple_acc:.2f}%')
print(f'Ensemble Weighted Scoring: {weighted_acc:.2f}%')
print(f'Difference: {weighted_acc - simple_acc:+.2f}%')
print()

if weighted_acc > simple_acc:
    print('Ket luan: Weighted Scoring TOT HON Simple Voting')
elif weighted_acc < simple_acc:
    print('Ket luan: Weighted Scoring KEM HON Simple Voting')
else:
    print('Ket luan: Ca 2 phuong phap BANG NHAU')
