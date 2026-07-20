"""Calculate proper random baseline for classification."""
import json
import numpy as np
from pathlib import Path
from math import comb

data = json.loads(Path('data/xsmn.json').read_text())

# Check how many unique numbers per draw
all_counts = []
for sample in data[:100]:  # Check first 100 records
    actual_nums = set()
    for k in sample:
        if k.startswith('prize') or k == 'special':
            val = sample[k]
            if val is not None and val != '' and val != 0:
                try:
                    n = int(str(val)[-2:])
                    actual_nums.add(n)
                except:
                    pass
    all_counts.append(len(actual_nums))

avg_actual = np.mean(all_counts)
print(f'Average unique numbers per draw: {avg_actual:.1f}')
print(f'Min: {min(all_counts)}, Max: {max(all_counts)}')
print()

# Calculate random baseline for 'at least 1 match in top 6'
n_predicted = 6
n_total = 100

for n_actual in [10, 12, 14, 16]:
    p_no_match = comb(n_total - n_actual, n_predicted) / comb(n_total, n_predicted)
    p_at_least_1 = 1 - p_no_match
    print(f'  If actual has {n_actual} numbers: P(at least 1 match) = {p_at_least_1*100:.2f}%')

print()
print(f'With avg {avg_actual:.0f} actual numbers:')
p_no_match = comb(n_total - int(avg_actual), n_predicted) / comb(n_total, n_predicted)
p_at_least_1 = 1 - p_no_match
print(f'  Random baseline: {p_at_least_1*100:.2f}%')
print()
print(f'LSTM Accuracy: 65.08%')
print(f'Random baseline: {p_at_least_1*100:.2f}%')
print()
if 65.08 > p_at_least_1 * 100:
    print('Ket luan: LSTM CO EDGE!')
else:
    print('Ket luan: LSTM KHONG CO EDGE')
