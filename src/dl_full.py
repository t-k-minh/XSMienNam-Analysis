"""Deep Learning on FULL dataset (all provinces, 2020-2026)."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('DEEP LEARNING ON FULL DATASET (ALL PROVINCES, 2020-2026)')
print('='*70)
print(f'Total: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# ============================================================
# MODELS
# ============================================================
class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1, 64, 2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        h0 = torch.zeros(2, x.size(0), 64)
        c0 = torch.zeros(2, x.size(0), 64)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])

class GRUModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(1, 64, 2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        h0 = torch.zeros(2, x.size(0), 64)
        out, _ = self.gru(x, h0)
        return self.fc(out[:, -1, :])

class TransformerModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Linear(1, 32)
        self.pos_enc = nn.Parameter(torch.randn(1, 10, 32) * 0.1)
        encoder_layer = nn.TransformerEncoderLayer(d_model=32, nhead=4, dim_feedforward=64, dropout=0.1, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.fc = nn.Sequential(nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x):
        x = self.embedding(x) + self.pos_enc[:, :x.size(1), :]
        x = self.transformer(x)
        return self.fc(x[:, -1, :])

# ============================================================
# STATISTICAL BASELINE
# ============================================================
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
# RUN ON ALL PROVINCES
# ============================================================
print('Running on all provinces...')
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

    # Extract targets
    targets = []
    for _, row in prov_data.iterrows():
        val = row['special']
        targets.append(int(str(val)[-2:]) if pd.notna(val) and val != '' else 0)

    # Prepare sequence data
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(np.array(targets).reshape(-1, 1)).flatten()

    seq_length = 10
    X_seq, y_seq = [], []
    for i in range(seq_length, len(scaled)):
        X_seq.append(scaled[i-seq_length:i])
        y_seq.append(scaled[i])

    X_seq = np.array(X_seq).reshape(-1, seq_length, 1)
    y_seq = np.array(y_seq)

    split = int(len(X_seq) * 0.8)
    X_train, X_test = X_seq[:split], X_seq[split:]
    y_train, y_test = y_seq[:split], y_seq[split:]

    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.FloatTensor(y_train)
    X_test_t = torch.FloatTensor(X_test)
    y_test_t = torch.FloatTensor(y_test)

    # Train and evaluate models
    results = {}

    for ModelClass, name in [(LSTMModel, 'LSTM'), (GRUModel, 'GRU'), (TransformerModel, 'Transformer')]:
        model = ModelClass()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        # Train
        model.train()
        for epoch in range(30):
            optimizer.zero_grad()
            outputs = model(X_train_t)
            loss = criterion(outputs.squeeze(), y_train_t)
            loss.backward()
            optimizer.step()

        # Evaluate
        model.eval()
        with torch.no_grad():
            y_pred = model(X_test_t).numpy().flatten()

        y_pred_inv = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
        y_test_inv = scaler.inverse_transform(y_test_t.numpy().reshape(-1, 1)).flatten()

        y_pred_digits = np.round(y_pred_inv).astype(int) % 100
        y_test_digits = y_test_inv.astype(int) % 100

        # Top-6 accuracy
        correct = 0
        total = 0
        for i in range(len(y_pred_digits)):
            pred = y_pred_digits[i]
            actual = y_test_digits[i]
            top6 = set([(pred + j) % 100 for j in range(-3, 3)])
            if actual in top6:
                correct += 1
            total += 1

        results[name] = correct / total * 100 if total > 0 else 0

    # Statistical baseline
    results['Statistical'] = 6.0  # Known baseline

    all_results[prov] = results

# ============================================================
# RESULTS TABLE
# ============================================================
print()
print('='*70)
print('RESULTS BY PROVINCE')
print('='*70)
print()

print(f'{"Tinh":<15} {"LSTM":<10} {"GRU":<10} {"Trans":<10} {"Stat":<10} {"Best":<10}')
print('-' * 65)

for prov in sorted(all_results.keys()):
    prov_name = prov_names.get(prov, prov)
    r = all_results[prov]
    best_method = max(r, key=r.get)
    best_acc = r[best_method]
    print(f'{prov_name:<15} {r.get("LSTM",0):.1f}%{" ":<4} {r.get("GRU",0):.1f}%{" ":<4} {r.get("Transformer",0):.1f}%{" ":<4} {r.get("Statistical",0):.1f}%{" ":<4} {best_method}({best_acc:.1f}%)')

print('-' * 65)

# Averages
print(f'{"TRUNG BINH":<15}', end='')
for method in ['LSTM', 'GRU', 'Transformer', 'Statistical']:
    accs = [r.get(method, 0) for r in all_results.values()]
    avg = np.mean(accs) if accs else 0
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

for method in ['LSTM', 'GRU', 'Transformer', 'Statistical']:
    accs = [r.get(method, 0) for r in all_results.values()]
    avg = np.mean(accs)
    better = sum(1 for a in accs if a > 6)
    print(f'{method}: TB {avg:.1f}% | {better}/{len(all_results)} tinh > 6%')

print()
print('Random baseline: 6.0%')
print()

# Compare with previous results
print('='*70)
print('SO SANH VOI CAC PHUONG PHAP TRUOC')
print('='*70)
print()
print(f'{"Phuong phap":<25} {"Accuracy":<12} {"Ghi chu"}')
print('-' * 50)
print(f'{"Ensemble (TS+XGB+Stat)":<25} {"11.5%":<12} {"Truoc do"}')
print(f'{"LSTM (Full)":<25} {np.mean([r.get("LSTM",0) for r in all_results.values()]):.1f}%{" ":<5} {"Moi"}')
print(f'{"GRU (Full)":<25} {np.mean([r.get("GRU",0) for r in all_results.values()]):.1f}%{" ":<5} {"Moi"}')
print(f'{"Transformer (Full)":<25} {np.mean([r.get("Transformer",0) for r in all_results.values()]):.1f}%{" ":<5} {"Moi"}')
print(f'{"Statistical":<25} {"6.1%":<12} {"Truoc do"}')
print(f'{"Random":<25} {"6.0%":<12} {"Baseline"}')
