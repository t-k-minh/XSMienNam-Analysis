"""Debug prediction differences."""
import json
import numpy as np
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

# Get TP.HCM data
hcm_data = [d for d in data if d['province'] == 'HCM']
hcm_data.sort(key=lambda x: x['date'])

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

# Test cutoff for 13/07 and 20/07
cutoff_13 = '2026-07-13'
cutoff_20 = '2026-07-20'

data_13 = [d for d in hcm_data if d['date'] < cutoff_13]
data_20 = [d for d in hcm_data if d['date'] < cutoff_20]

print(f'Data before 13/07: {len(data_13)} records')
print(f'Data before 20/07: {len(data_20)} records')
print()

# Statistical prediction
stat_13 = calc_scores(data_13)
stat_20 = calc_scores(data_20)

print('Statistical Top 6 for 13/07:', [n for n, s in stat_13[:6]])
print('Statistical Top 6 for 20/07:', [n for n, s in stat_20[:6]])
print()

# Thompson prediction
np.random.seed(42)
thompson_13 = thompson_predict(data_13)
thompson_20 = thompson_predict(data_20)

print('Thompson Top 6 for 13/07:', sorted(thompson_13))
print('Thompson Top 6 for 20/07:', sorted(thompson_20))
print()

# Ensemble
def ensemble(data):
    stat = set([n for n, s in calc_scores(data)[:6]])
    thompson = thompson_predict(data)
    votes = {}
    for n in stat:
        votes[n] = votes.get(n, 0) + 1
    for n in thompson:
        votes[n] = votes.get(n, 0) + 1
    return set(sorted(votes.keys(), key=lambda x: votes[x], reverse=True)[:6])

ens_13 = ensemble(data_13)
ens_20 = ensemble(data_20)

print('Ensemble Top 6 for 13/07:', sorted(ens_13))
print('Ensemble Top 6 for 20/07:', sorted(ens_20))
print()
print('Same prediction?', ens_13 == ens_20)
