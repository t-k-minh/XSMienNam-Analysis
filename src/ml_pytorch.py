"""Machine Learning analysis using PyTorch LSTM."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*60)
print('PYTORCH LSTM ANALYSIS FOR XSMN LOTTERY')
print('='*60)
print(f'Data: {len(df)} records, {df["province"].nunique()} provinces')
print(f'Date range: {df["date"].min().date()} to {df["date"].max().date()}')
print()

# ============================================================
# 1. FEATURE ENGINEERING
# ============================================================
print('=== 1. FEATURE ENGINEERING ===')
print()

def create_features(df_prov, target_col='special'):
    df_prov = df_prov.sort_values('date').reset_index(drop=True)
    df_prov['target'] = df_prov[target_col].apply(lambda x: int(str(x)[-2:]) if pd.notna(x) else None)

    # Lag features
    for lag in range(1, 8):
        df_prov[f'lag_{lag}'] = df_prov['target'].shift(lag)

    # Rolling statistics
    for window in [7, 14, 30]:
        df_prov[f'rolling_mean_{window}'] = df_prov['target'].rolling(window).mean()
        df_prov[f'rolling_std_{window}'] = df_prov['target'].rolling(window).std()

    return df_prov

# Process TP.HCM
sample_prov = 'HCM'
df_hcm = df[df['province'] == sample_prov].copy()
df_hcm = create_features(df_hcm)
df_hcm = df_hcm.dropna()

print(f'Sample province: {sample_prov}')
print(f'Records: {len(df_hcm)}')
print()

# ============================================================
# 2. LSTM MODEL (PyTorch)
# ============================================================
print('=== 2. LSTM MODEL (PyTorch) ===')
print()

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 25),
            nn.ReLU(),
            nn.Linear(25, output_size)
        )

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Prepare sequence data
sequence_length = 10
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

values = df_hcm['target'].values.reshape(-1, 1)
scaled_values = scaler.fit_transform(values)

# Create sequences
X_seq, y_seq = [], []
for i in range(sequence_length, len(scaled_values)):
    X_seq.append(scaled_values[i-sequence_length:i, 0])
    y_seq.append(scaled_values[i, 0])

X_seq = np.array(X_seq)
y_seq = np.array(y_seq)

# Reshape for LSTM [samples, timesteps, features]
X_seq = X_seq.reshape((X_seq.shape[0], X_seq.shape[1], 1))

# Split train/test (80/20)
split = int(len(X_seq) * 0.8)
X_train, X_test = X_seq[:split], X_seq[split:]
y_train, y_test = y_seq[:split], y_seq[split:]

# Convert to tensors
X_train_tensor = torch.FloatTensor(X_train)
y_train_tensor = torch.FloatTensor(y_train)
X_test_tensor = torch.FloatTensor(X_test)
y_test_tensor = torch.FloatTensor(y_test)

# Create DataLoader
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

# Initialize model
model = LSTMModel(input_size=1, hidden_size=50, num_layers=2, output_size=1)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Train
print('Training LSTM...')
epochs = 50
train_losses = []

for epoch in range(epochs):
    model.train()
    epoch_loss = 0
    for batch_X, batch_y in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs.squeeze(), batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(train_loader)
    train_losses.append(avg_loss)

    if (epoch + 1) % 10 == 0:
        print(f'  Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}')

print()

# Evaluate
model.eval()
with torch.no_grad():
    y_pred = model(X_test_tensor).numpy().flatten()

# Inverse transform
y_pred_inv = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

# Calculate metrics
mae = np.mean(np.abs(y_pred_inv - y_test_inv))
rmse = np.sqrt(np.mean((y_pred_inv - y_test_inv)**2))

# Convert to 2-digit and check exact match
y_pred_digits = np.round(y_pred_inv).astype(int) % 100
y_test_digits = y_test_inv.astype(int) % 100
exact_match = np.mean(y_pred_digits == y_test_digits) * 100

# Check if predicted number is within +/- 5 of actual
within_5 = 0
for i in range(len(y_test_digits)):
    actual = y_test_digits[i]
    predicted = y_pred_digits[i]
    diff = abs(predicted - actual)
    if diff <= 5 or diff >= 95:  # 95 because 99+1=100, wraps around
        within_5 += 1

print('=== LSTM RESULTS ===')
print(f'MAE: {mae:.2f}')
print(f'RMSE: {rmse:.2f}')
print(f'Exact match: {exact_match:.2f}%')
print(f'Within +/- 5: {within_5/len(y_test_digits)*100:.2f}%')
print(f'Random baseline: 1.00%')
print()

# ============================================================
# 3. CLASSIFICATION VERSION (predict which number will appear)
# ============================================================
print('=== 3. CLASSIFICATION LSTM ===')
print()

# For classification: predict top 6 numbers for next draw
class LSTMPredictor(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=100):
        super(LSTMPredictor, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_size),
            nn.Sigmoid()
        )

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Create multi-label targets (which numbers appeared)
def create_multilabel_target(record, num_cols=100):
    target = np.zeros(num_cols)
    for k in record:
        if k.startswith('prize') or k == 'special':
            val = record[k]
            if val is not None and val != '' and val != 0:
                try:
                    n = int(str(val)[-2:])
                    target[n] = 1
                except:
                    pass
    return target

# Prepare data for classification
df_hcm_class = df[df['province'] == sample_prov].sort_values('date').reset_index(drop=True)
records = df_hcm_class.to_dict('records')

# Create sequences with multi-label targets
seq_length = 10
X_class, y_class = [], []
for i in range(seq_length, len(records)):
    # Features: last 2 digits of each prize
    features = []
    for j in range(i-seq_length, i):
        feat = []
        for k in records[j]:
            if k.startswith('prize') or k == 'special':
                val = records[j][k]
                if val is not None and val != '' and val != 0:
                    try:
                        feat.append(int(str(val)[-2:]) / 99.0)  # Normalize
                    except:
                        feat.append(0)
                else:
                    feat.append(0)
        features.append(feat[:15])  # Use 15 prize values
    X_class.append(features)
    y_class.append(create_multilabel_target(records[i]))

X_class = np.array(X_class)
y_class = np.array(y_class)

print(f'Classification data: {len(X_class)} samples')
print(f'Features per timestep: {X_class.shape[2]}')
print()

# Build classification model
class LSTMBinaryClassifier(nn.Module):
    def __init__(self, input_size=15, hidden_size=64, num_layers=2, output_size=100):
        super(LSTMBinaryClassifier, self).__init__()
        self.num_layers = num_layers
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_size),
            nn.Sigmoid()
        )

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Split data
split = int(len(X_class) * 0.8)
X_train_c = torch.FloatTensor(X_class[:split])
y_train_c = torch.FloatTensor(y_class[:split])
X_test_c = torch.FloatTensor(X_class[split:])
y_test_c = torch.FloatTensor(y_class[split:])

# Build model
model_class = LSTMBinaryClassifier(input_size=15, hidden_size=64, num_layers=2, output_size=100)
criterion_class = nn.BCELoss()
optimizer_class = torch.optim.Adam(model_class.parameters(), lr=0.001)

# Train
print('Training Classification LSTM...')
for epoch in range(30):
    model_class.train()
    optimizer_class.zero_grad()
    outputs = model_class(X_train_c)
    loss = criterion_class(outputs, y_train_c)
    loss.backward()
    optimizer_class.step()

    if (epoch + 1) % 10 == 0:
        print(f'  Epoch {epoch+1}/30, Loss: {loss.item():.4f}')

# Evaluate
model_class.eval()
with torch.no_grad():
    y_pred_class = model_class(X_test_c).numpy()

# Get top 6 predicted numbers for each test sample
correct = 0
total = 0
for i in range(len(y_pred_class)):
    predicted_top6 = set(np.argsort(y_pred_class[i])[-6:])
    actual_nums = set(np.where(y_test_c[i].numpy() == 1)[0])
    if predicted_top6 & actual_nums:  # Check intersection
        correct += 1
    total += 1

accuracy = correct / total * 100

print()
print('=== CLASSIFICATION LSTM RESULTS ===')
print(f'Accuracy (at least 1 match in top 6): {accuracy:.2f}%')
print(f'Random baseline (6/100): 6.00%')
print()

# ============================================================
# 4. CONCLUSION
# ============================================================
print('=== 4. KET LUAN ===')
print()
print('Regression LSTM:')
print(f'  - Exact match: {exact_match:.2f}% (random: 1.00%)')
print(f'  - Within +/- 5: {within_5/len(y_test_digits)*100:.2f}%')
print()
print('Classification LSTM:')
print(f'  - Accuracy: {accuracy:.2f}% (random: 6.00%)')
print()
if accuracy > 7:
    print('Ket luan: Classification LSTM CO EDGE nho')
else:
    print('Ket luan: Ca 2 model deu KHONG tim duoc pattern')
    print('Xo so that su ngau nhien')
