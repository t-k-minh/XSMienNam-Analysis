"""Run backtest analysis on XSMN data."""
import json
from datetime import datetime, timedelta
from pathlib import Path

# Load data
data = json.loads(Path('data/xsmn.json').read_text())

print('=== THONG KE DU LIEU ===')
print(f'Tong so ban ghi: {len(data)}')
provinces = set(d['province'] for d in data)
print(f'So tinh: {len(provinces)}')
dates = set(d['date'] for d in data)
print(f'So ngay: {len(dates)}')
print(f'Ngay dau tien: {min(dates)}')
print(f'Ngay cuoi cung: {max(dates)}')
print()


def calc_scores(records):
    """Calculate ML scores for numbers 00-99."""
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
                    except:
                        pass
    total = len(records)
    scores = {}
    for i in range(100):
        fs = freq[i] / (total * 0.2) if total > 0 else 0
        od = total - 1 - (ls[i] if ls[i] != -1 else 0)
        os_val = min(od / 50, 1)
        scores[i] = fs * 0.5 + os_val * 0.5
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return set([n for n, s in sorted_scores[:6]])


def get_actual_numbers(record):
    """Get actual 2-digit numbers from a record."""
    nums = set()
    for k in record:
        if k.startswith('prize') or k == 'special':
            val = record[k]
            if val is not None and val != '' and val != 0:
                try:
                    n = int(str(val)[-2:])
                    nums.add(n)
                except:
                    pass
    return nums


# Province names
prov_names = {
    'AG': 'An Giang', 'BD': 'Binh Duong', 'BL': 'Bac Lieu', 'BP': 'Binh Phuoc',
    'BTH': 'Binh Thuan', 'BTR': 'Ben Tre', 'CM': 'Ca Mau', 'CT': 'Can Tho',
    'DL': 'Da Lat', 'DNA': 'Dong Nai', 'DT': 'Dong Thap', 'HCM': 'TP.HCM',
    'HGG': 'Hau Giang', 'KG': 'Kien Giang', 'LA': 'Long An', 'ST': 'Soc Trang',
    'TGI': 'Tien Giang', 'TNI': 'Tay Ninh', 'TV': 'Tra Vinh', 'VL': 'Vinh Long',
    'VT': 'Vung Tau'
}

# Run backtest for each province
print('=== KET QUA BACKTEST ===')
print()

results = {}
for prov in sorted(provinces):
    prov_data = [d for d in data if d['province'] == prov]
    prov_data.sort(key=lambda x: x['date'])

    if len(prov_data) < 50:
        continue

    prov_name = prov_names.get(prov, prov)

    # Test on last 20%
    test_size = int(len(prov_data) * 0.2)
    train_end = len(prov_data) - test_size

    # Test with different windows
    for win_name, win_days in [('30 ngay', 30), ('3 thang', 90), ('6 thang', 180), ('1 nam', 365), ('Tat ca', 0)]:
        correct = 0
        total = 0

        for i in range(train_end, len(prov_data)):
            test_record = prov_data[i]
            test_date = test_record['date']

            # Get training data
            train_data = [d for d in prov_data if d['date'] < test_date]
            if win_days > 0:
                cutoff = datetime.strptime(test_date, '%Y-%m-%d') - timedelta(days=win_days)
                cutoff_str = cutoff.strftime('%Y-%m-%d')
                train_data = [d for d in train_data if d['date'] >= cutoff_str]

            if len(train_data) < 10:
                continue

            # Predict
            predicted = calc_scores(train_data)

            # Get actual
            actual = get_actual_numbers(test_record)

            # Count matches
            matches = predicted & actual
            correct += len(matches)
            total += 1

        if prov not in results:
            results[prov] = {}
        acc = (correct / total * 100) if total > 0 else 0
        results[prov][win_name] = {'acc': acc, 'correct': correct, 'total': total}

# Print results table
windows = ['30 ngay', '3 thang', '6 thang', '1 nam', 'Tat ca']

print(f'{"Tinh":<15}', end='')
for w in windows:
    print(f'{w:<12}', end='')
print('Ngau nhien')
print('-' * 85)

for prov in sorted(results.keys()):
    prov_name = prov_names.get(prov, prov)
    print(f'{prov_name:<15}', end='')
    for w in windows:
        acc = results[prov][w]['acc']
        print(f'{acc:<12.1f}', end='')
    print('6.0%')

# Calculate averages
print('-' * 85)
print(f'{"Trung binh":<15}', end='')
for w in windows:
    avg = sum(results[p][w]['acc'] for p in results) / len(results)
    print(f'{avg:<12.1f}', end='')
print('6.0%')

# Analysis
print()
print('=== PHAN TICH ===')
print()

for w in windows:
    avg = sum(results[p][w]['acc'] for p in results) / len(results)
    better = sum(1 for p in results if results[p][w]['acc'] > 6.0)
    print(f'{w}: Trung binh {avg:.1f}% | {better}/{len(results)} tinh tot hon ngau nhien')

print()
best_w = max(windows, key=lambda w: sum(results[p][w]['acc'] for p in results) / len(results))
worst_w = min(windows, key=lambda w: sum(results[p][w]['acc'] for p in results) / len(results))
print(f'Ket luan:')
print(f'- Khoang thoi gian tot nhat: {best_w}')
print(f'- Khoang thoi gian kem nhat: {worst_w}')

if sum(results[p][best_w]['acc'] for p in results) / len(results) > 7.0:
    print('- Mo hinh co EDGE nho so voi ngau nhien')
else:
    print('- Mo hinh KHONG co edge ro rang so voi ngau nhien')
    print('- Ket qua ~6% cho thay xso that su ngau nhien')
