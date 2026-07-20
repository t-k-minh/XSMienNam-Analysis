"""Run corrected backtest - only special prize last 2 digits."""
import json
from datetime import datetime, timedelta
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

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
    return set([n for n, s in sorted_scores[:6]])

prov_names = {
    'AG': 'An Giang', 'BD': 'Binh Duong', 'BL': 'Bac Lieu', 'BP': 'Binh Phuoc',
    'BTH': 'Binh Thuan', 'BTR': 'Ben Tre', 'CM': 'Ca Mau', 'CT': 'Can Tho',
    'DL': 'Da Lat', 'DNA': 'Dong Nai', 'DT': 'Dong Thap', 'HCM': 'TP.HCM',
    'HGG': 'Hau Giang', 'KG': 'Kien Giang', 'LA': 'Long An', 'ST': 'Soc Trang',
    'TGI': 'Tien Giang', 'TNI': 'Tay Ninh', 'TV': 'Tra Vinh', 'VL': 'Vinh Long',
    'VT': 'Vung Tau'
}

print('=== BACKTEST: Chi lay so cuoi GIAI DAC BIET ===')
print('Phuong phap: Du doan top 6 so, kiem tra 2 so cuoi GDB co nam trong top 6')
print('Ngau nhien = 6/100 = 6.0%')
print()

results = {}
for prov in sorted(set(d['province'] for d in data)):
    prov_data = sorted([d for d in data if d['province'] == prov], key=lambda x: x['date'])
    if len(prov_data) < 50:
        continue

    prov_name = prov_names.get(prov, prov)
    test_size = int(len(prov_data) * 0.2)
    train_end = len(prov_data) - test_size

    results[prov] = {}
    for win_name, win_days in [('3 thang', 90), ('6 thang', 180), ('1 nam', 365), ('Tat ca', 0)]:
        hits = 0
        total = 0

        for i in range(train_end, len(prov_data)):
            test_date = prov_data[i]['date']
            train_data = [d for d in prov_data if d['date'] < test_date]
            if win_days > 0:
                cutoff = datetime.strptime(test_date, '%Y-%m-%d') - timedelta(days=win_days)
                cutoff_str = cutoff.strftime('%Y-%m-%d')
                train_data = [d for d in train_data if d['date'] >= cutoff_str]

            if len(train_data) < 10:
                continue

            predicted = calc_scores(train_data)
            actual_special = prov_data[i].get('special')
            if not actual_special:
                continue
            actual_num = int(str(actual_special)[-2:])
            total += 1
            if actual_num in predicted:
                hits += 1

        acc = (hits / total * 100) if total > 0 else 0
        results[prov][win_name] = acc

# Print table
windows = ['3 thang', '6 thang', '1 nam', 'Tat ca']
print(f'{"Tinh":<15}', end='')
for w in windows:
    print(f'{w:<12}', end='')
print('Ngau nhien')
print('-' * 70)

for prov in sorted(results.keys()):
    prov_name = prov_names.get(prov, prov)
    print(f'{prov_name:<15}', end='')
    for w in windows:
        acc = results[prov][w]
        marker = '*' if acc > 7 else ' '
        print(f'{acc:.1f}%{marker:<6}', end='')
    print('6.0%')

print('-' * 70)
print(f'{"Trung binh":<15}', end='')
for w in windows:
    avg = sum(results[p][w] for p in results) / len(results)
    print(f'{avg:.1f}%{" ":<6}', end='')
print('6.0%')

print()
print('=== PHAN TICH ===')
for w in windows:
    avg = sum(results[p][w] for p in results) / len(results)
    better = sum(1 for p in results if results[p][w] > 6.0)
    print(f'{w}: TB {avg:.1f}% | {better}/{len(results)} tinh > 6%')
