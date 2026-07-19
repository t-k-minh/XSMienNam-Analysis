"""Deep Learning comparison: LSTM, GRU, Transformer-lite."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*70)
print('DEEP LEARNING COMPARISON FOR XSMN LOTTERY')
print('='*70)
print(f'Data: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Date range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# Use TP.HCM
hcm_data = df[df['province'] == 'HCM'].sort_values('date')
print(f'TP.HCM: {len(hcm_data)} records')
print()

# ============================================================
# PREPARE DATA
# ============================================================
# Extract special prize last 2 digits
targets = []
for _, row in hcm_data.iterrows():
    val = row['special']
    if pd.notna(val):
        targets.append(int(str(val)[-2:]))
    else:
        targets.append(0)

targets = np.array(targets)

# Normalize
scaler = MinMaxScaler()
scaled = scaler.fit_transform(targets.reshape(-1, 1)).flatten()

# Create sequences
seq_length = 10
X_seq, y_seq = [], []
for i in range(seq_length, len(scaled)):
    X_seq.append(scaled[i-seq_length:i])
    y_seq.append(scaled[i])

X_seq = np.array(X_seq)
y_seq = np.array(y_seq)

# Reshape for models [samples, timesteps, features]
X_seq = X_seq.reshape((X_seq.shape[0], X_seq.shape[1], 1))

# Split train/test (80/20)
split = int(len(X_seq) * 0.8)
X_train, X_test = X_seq[:split], X_seq[split:]
y_train, y_test = y_seq[:split], y_seq[split:]

# Convert to tensors
X_train_t = torch.FloatTensor(X_train)
y_train_t = torch.FloatTensor(y_train)
X_test_t = torch.FloatTensor(X_test)
y_test_t = torch.FloatTensor(y_test)

print(f'Train: {len(X_train)}, Test: {len(X_test)}')
print()

# ============================================================
# MODEL 1: LSTM
# ============================================================
class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(1, 50, 2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(nn.Linear(50, 25), nn.ReLU(), nn.Linear(25, 1))

    def forward(self, x):
        h0 = torch.zeros(2, x.size(0), 50)
        c0 = torch.zeros(2, x.size(0), 50)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])

# ============================================================
# MODEL 2: GRU
# ============================================================
class GRUModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(1, 50, 2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(nn.Linear(50, 25), nn.ReLU(), nn.Linear(25, 1))

    def forward(self, x):
        h0 = torch.zeros(2, x.size(0), 50)
        out, _ = self.gru(x, h0)
        return self.fc(out[:, -1, :])

# ============================================================
# MODEL 3: Transformer-lite
# ============================================================
class TransformerLite(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Linear(1, 32)
        self.pos_enc = nn.Parameter(torch.randn(1, 10, 32) * 0.1)
        self.attention = nn.MultiheadAttention(32, 4, batch_first=True)
        self.fc = nn.Sequential(nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x):
        x = self.embedding(x) + self.pos_enc[:, :x.size(1), :]
        x, _ = self.attention(x, x, x)
        return self.fc(x[:, -1, :])

# ============================================================
# TRAIN AND EVALUATE
# ============================================================
def train_and_evaluate(model, name, epochs=50):
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_train_t)
        loss = criterion(outputs.squeeze(), y_train_t)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        y_pred = model(X_test_t).numpy().flatten()

    # Metrics
    y_pred_inv = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    y_test_inv = scaler.inverse_transform(y_test_t.numpy().reshape(-1, 1)).flatten()

    mae = np.mean(np.abs(y_pred_inv - y_test_inv))
    rmse = np.sqrt(np.mean((y_pred_inv - y_test_inv)**2))

    # Exact match
    y_pred_digits = np.round(y_pred_inv).astype(int) % 100
    y_test_digits = y_test_inv.astype(int) % 100
    exact_match = np.mean(y_pred_digits == y_test_digits) * 100

    # Within +/- 5
    within_5 = np.mean(np.abs(y_pred_digits - y_test_digits) <= 5) * 100

    # Top-6 accuracy (is actual in top 6 closest to predicted?)
    top6_correct = 0
    for i in range(len(y_pred_digits)):
        pred = y_pred_digits[i]
        actual = y_test_digits[i]
        # Generate top 6 numbers around predicted
        top6 = set([(pred + j) % 100 for j in range(-3, 3)])
        if actual in top6:
            top6_correct += 1
    top6_acc = top6_correct / len(y_pred_digits) * 100

    return {
        'name': name,
        'mae': mae,
        'rmse': rmse,
        'exact_match': exact_match,
        'within_5': within_5,
        'top6_acc': top6_acc
    }

# ============================================================
# RUN ALL MODELS
# ============================================================
print('Training models...')
print()

results = []

# LSTM
print('Training LSTM...')
lstm_model = LSTMModel()
results.append(train_and_evaluate(lstm_model, 'LSTM'))

# GRU
print('Training GRU...')
gru_model = GRUModel()
results.append(train_and_evaluate(gru_model, 'GRU'))

# Transformer
print('Training Transformer...')
transformer_model = TransformerLite()
results.append(train_and_evaluate(transformer_model, 'Transformer'))

# Statistical baseline
print('Calculating Statistical baseline...')
# Simple moving average prediction
stat_preds = []
for i in range(seq_length, len(scaled)):
    window = scaled[i-seq_length:i]
    stat_preds.append(np.mean(window))

stat_preds = np.array(stat_preds[split:])
stat_pred_inv = scaler.inverse_transform(stat_preds.reshape(-1, 1)).flatten()
y_test_inv = scaler.inverse_transform(y_test_t.numpy().reshape(-1, 1)).flatten()

stat_mae = np.mean(np.abs(stat_pred_inv - y_test_inv))
stat_rmse = np.sqrt(np.mean((stat_pred_inv - y_test_inv)**2))
stat_pred_digits = np.round(stat_pred_inv).astype(int) % 100
stat_exact = np.mean(stat_pred_digits == y_test_inv.astype(int) % 100) * 100
stat_within_5 = np.mean(np.abs(stat_pred_digits - y_test_inv.astype(int) % 100) <= 5) * 100
stat_top6 = np.mean([1 if abs(stat_pred_digits[i] - (y_test_inv.astype(int)%100)[i]) <= 3 or abs(stat_pred_digits[i] - (y_test_inv.astype(int)%100)[i]) >= 97 else 0 for i in range(len(stat_pred_digits))]) * 100

results.append({
    'name': 'Statistical (SMA)',
    'mae': stat_mae,
    'rmse': stat_rmse,
    'exact_match': stat_exact,
    'within_5': stat_within_5,
    'top6_acc': stat_top6
})

# Random baseline
results.append({
    'name': 'Random',
    'mae': 25.0,
    'rmse': 30.0,
    'exact_match': 1.0,
    'within_5': 11.0,
    'top6_acc': 6.0
})

# ============================================================
# RESULTS TABLE
# ============================================================
print()
print('='*70)
print('RESULTS COMPARISON')
print('='*70)
print()

print(f'{"Model":<20} {"MAE":<8} {"RMSE":<8} {"Exact%":<10} {"Within5%":<10} {"Top6%":<10}')
print('-' * 70)

for r in results:
    print(f'{r["name"]:<20} {r["mae"]:<8.2f} {r["rmse"]:<8.2f} {r["exact_match"]:<10.2f} {r["within_5"]:<10.2f} {r["top6_acc"]:<10.2f}')

print('-' * 70)
print()

# ============================================================
# ANALYSIS
# ============================================================
print('='*70)
print('PHAN TICH')
print('='*70)
print()

# Find best models
best_exact = max(results, key=lambda x: x['exact_match'])
best_within5 = max(results, key=lambda x: x['within_5'])
best_top6 = max(results, key=lambda x: x['top6_acc'])

print(f'Best Exact Match: {best_exact["name"]} ({best_exact["exact_match"]:.2f}%)')
print(f'Best Within +/-5: {best_within5["name"]} ({best_within5["within_5"]:.2f}%)')
print(f'Best Top-6: {best_top6["name"]} ({best_top6["top6_acc"]:.2f}%)')
print()

# Compare with random
print('So sanh voi Random Baseline:')
for r in results:
    if r['name'] != 'Random':
        diff = r['exact_match'] - 1.0
        status = 'TOT HON' if diff > 0.5 else ('BANG' if diff > -0.5 else 'KEM HON')
        print(f'  {r["name"]}: {r["exact_match"]:.2f}% (random: 1.00%) -> {status} {diff:+.2f}%')

print()
print('='*70)
print('KET LUAN')
print('='*70)
print()

if best_exact['exact_match'] > 2:
    print(f'{best_exact["name"]} co EDGE nho ({best_exact["exact_match"]:.2f}% vs 1.00% random)')
else:
    print('Ca LSTM, GRU, Transformer deu KHONG co edge ro rang so voi ngau nhien')
    print('Xo so that su ngau nhien - khong co AI nao du doan duoc')
