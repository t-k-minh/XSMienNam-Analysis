"""Run backtest analysis on XSMN data - FIXED VERSION."""
import json
from datetime import datetime, timedelta
from pathlib import Path

# Load data
data = json.loads(Path('data/xsmn.json').read_text())

print('=== THONG KE DU LIEU ===')
print(f'Tong so ban ghi: {len(data)}')
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


def get_last2_numbers(record):
    """Get the 2-digit ending of SPECIAL prize only."""
    val = record.get('special')
    if val is not None and val != '' and val != 0:
        try:
            return int(str(val)[-2:])
        except:
            pass
    return None


# Province names
prov_names = {
    'AG': 'An Giang', 'BD': 'Binh Duong', 'BL': 'Bac Lieu', 'BP': 'Binh Phuoc',
    'BTH': 'Binh Thuan', 'BTR': 'Ben Tre', 'CM': 'Ca Mau', 'CT': 'Can Tho',
    'DL': 'Da Lat', 'DNA': 'Dong Nai', 'DT': 'Dong Thap', 'HCM': 'TP.HCM',
    'HGG': 'Hau Giang', 'KG': 'Kien Giang', 'LA': 'Long An', 'ST': 'Soc Trang',
    'TGI': 'Tien Giang', 'TNI': 'Tay Ninh', 'TV': 'Tra Vinh', 'VL': 'Vinh Long',
    'VT': 'Vung Tau'
}

# Run backtest for a few provinces
test_provinces = ['HCM', 'TNI', 'DNA', 'AG', 'BTH']
print('=== KET QUA BACKTEST (chi so special prize) ===')
print()
print('Phuong phap: Du doan top 6 so, kiem tra so cuoi cua GIAI DAC BIET')
print('Accuracy = so lan trung / so ky test')
print('Ngau nhien = 6/100 = 6%')
print()

for prov in test_provinces:
    prov_data = [d for d in data if d['province'] == prov]
    prov_data.sort(key=lambda x: x['date'])

    if len(prov_data) < 50:
        continue

    prov_name = prov_names.get(prov, prov)

    # Test on last 20%
    test_size = int(len(prov_data) * 0.2)
    train_end = len(prov_data) - test_size

    print(f'--- {prov_name} ({len(prov_data)} ky, test {test_size} ky) ---')

    for win_name, win_days in [('3 thang', 90), ('6 thang', 180), ('1 nam', 365), ('Tat ca', 0)]:
        correct = 0
        total = 0
        total_matches = 0

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

            # Predict top 6
            predicted = calc_scores(train_data)

            # Get actual special prize last 2 digits
            actual = get_last2_numbers(test_record)

            if actual is not None:
                total += 1
                if actual in predicted:
                    correct += 1

        acc = (correct / total * 100) if total > 0 else 0
        print(f'  {win_name:<10}: {acc:.1f}% ({correct}/{total})')

    print()

# Overall summary
print('=== TONG KET ===')
print('Neu accuracy > 6% lien tuc: Mo hinh co EDGE')
print('Neu accuracy ~ 6%: Khong khac ngau nhien')
print('Neu accuracy < 6: Mo hinh kem hon ngau nhien')
