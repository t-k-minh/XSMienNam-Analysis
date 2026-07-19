"""Machine Learning analysis for XSMN lottery data."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# Load data
data = json.loads(Path('data/xsmn.json').read_text())
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['province', 'date'])

print('='*60)
print('MACHINE LEARNING ANALYSIS FOR XSMN LOTTERY')
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
    """Create features for ML model."""
    df_prov = df_prov.sort_values('date').reset_index(drop=True)

    # Extract last 2 digits of special prize
    df_prov['target'] = df_prov[target_col].apply(lambda x: int(str(x)[-2:]) if pd.notna(x) else None)

    # Time-based features
    df_prov['day_of_week'] = df_prov['date'].dt.dayofweek
    df_prov['day_of_month'] = df_prov['date'].dt.day
    df_prov['month'] = df_prov['date'].dt.month
    df_prov['week_of_year'] = df_prov['date'].dt.isocalendar().week.astype(int)

    # Lag features (previous results)
    for lag in range(1, 8):
        df_prov[f'lag_{lag}'] = df_prov['target'].shift(lag)

    # Rolling statistics
    for window in [7, 14, 30]:
        df_prov[f'rolling_mean_{window}'] = df_prov['target'].rolling(window).mean()
        df_prov[f'rolling_std_{window}'] = df_prov['target'].rolling(window).std()
        df_prov[f'rolling_min_{window}'] = df_prov['target'].rolling(window).min()
        df_prov[f'rolling_max_{window}'] = df_prov['target'].rolling(window).max()

    # Frequency features (last N days)
    for window in [7, 14, 30]:
        df_prov[f'freq_last_{window}'] = df_prov['target'].rolling(window).apply(
            lambda x: len(set(x.dropna().astype(int).tolist())), raw=False
        )

    # Overdue features
    df_prov['days_since_last'] = df_prov['target'].apply(
        lambda x: 0 if pd.isna(x) else None
    )
    for i in range(len(df_prov)):
        if pd.notna(df_prov.loc[i, 'target']):
            val = df_prov.loc[i, 'target']
            for j in range(i-1, -1, -1):
                if df_prov.loc[j, 'target'] == val:
                    df_prov.loc[i, 'days_since_last'] = i - j
                    break
            if df_prov.loc[i, 'days_since_last'] is None:
                df_prov.loc[i, 'days_since_last'] = i + 1

    return df_prov

# Process one province as example
sample_prov = 'HCM'
df_hcm = df[df['province'] == sample_prov].copy()
df_hcm = create_features(df_hcm)
df_hcm = df_hcm.dropna()

print(f'Sample province: {sample_prov}')
print(f'Records after feature engineering: {len(df_hcm)}')
print(f'Features created: {len(df_hcm.columns) - 2}')  # Exclude date and original special
print()

# ============================================================
# 2. RANDOM FOREST
# ============================================================
print('=== 2. RANDOM FOREST ===')
print()

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report

# Prepare features
feature_cols = [c for c in df_hcm.columns if c not in ['date', 'special', 'target', 'province']]
X = df_hcm[feature_cols].values
y = df_hcm['target'].values

# Time series split (no shuffle)
tscv = TimeSeriesSplit(n_splits=5)

rf_scores = []
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    score = accuracy_score(y_test, y_pred)
    rf_scores.append(score)

print(f'Random Forest Accuracy (5-fold time series CV):')
print(f'  Mean: {np.mean(rf_scores)*100:.2f}%')
print(f'  Std: {np.std(rf_scores)*100:.2f}%')
print(f'  Random baseline: 1/100 = 1.00%')
print()

# Feature importance
rf_full = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_full.fit(X, y)
importances = rf_full.feature_importances_
feature_importance = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)

print('Top 10 Feature Importance:')
for feat, imp in feature_importance[:10]:
    print(f'  {feat}: {imp:.4f}')
print()

# ============================================================
# 3. LSTM (Simple)
# ============================================================
print('=== 3. LSTM (Simple Sequence Model) ===')
print()

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import MinMaxScaler

    # Prepare sequence data
    sequence_length = 10
    scaler = MinMaxScaler()

    # Use only target values for simple LSTM
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

    # Build LSTM model
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(sequence_length, 1)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Train
    history = model.fit(
        X_train, y_train,
        batch_size=16,
        epochs=50,
        validation_split=0.1,
        verbose=0
    )

    # Predict
    y_pred = model.predict(X_test, verbose=0)
    y_pred_inv = scaler.inverse_transform(y_pred).flatten()
    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

    # Calculate accuracy (how close predictions are to actual)
    mae = np.mean(np.abs(y_pred_inv - y_test_inv))
    rmse = np.sqrt(np.mean((y_pred_inv - y_test_inv)**2))

    # Convert to 2-digit and check exact match
    y_pred_digits = np.round(y_pred_inv).astype(int) % 100
    y_test_digits = y_test_inv.astype(int) % 100
    exact_match = np.mean(y_pred_digits == y_test_digits) * 100

    # Check if predicted number is in top 6 closest to actual
    top6_correct = 0
    for i in range(len(y_test_digits)):
        actual = y_test_digits[i]
        predicted = y_pred_digits[i]
        # Check if predicted is within +/- 5 of actual
        if abs(predicted - actual) <= 5 or abs(predicted - actual) >= 95:
            top6_correct += 1

    print(f'LSTM Results:')
    print(f'  MAE: {mae:.2f}')
    print(f'  RMSE: {rmse:.2f}')
    print(f'  Exact match: {exact_match:.2f}%')
    print(f'  Within +/- 5: {top6_correct/len(y_test_digits)*100:.2f}%')
    print(f'  Random baseline: 1.00%')
    print()

except ImportError:
    print('TensorFlow not installed. Skipping LSTM analysis.')
    print('Install with: pip install tensorflow')
    print()

# ============================================================
# 4. PATTERN ANALYSIS
# ============================================================
print('=== 4. PATTERN ANALYSIS ===')
print()

# Check for cyclical patterns
df_all = df.copy()
df_all['day_of_week'] = df_all['date'].dt.dayofweek
df_all['target'] = df_all['special'].apply(lambda x: int(str(x)[-2:]) if pd.notna(x) else None)
df_all = df_all.dropna(subset=['target'])

# Frequency by day of week
print('Frequency by Day of Week (last 2 digits of special prize):')
day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
for day in range(7):
    day_data = df_all[df_all['day_of_week'] == day]['target']
    if len(day_data) > 0:
        top3 = day_data.value_counts().head(3)
        print(f'  {day_names[day]}: Top 3 = {list(top3.index)} (counts: {list(top3.values)})')

print()

# Check for hot/cold numbers
print('Overall Hot/Cold Numbers (all provinces, all time):')
all_targets = df_all['target'].values
target_counts = Counter(all_targets)
hot_10 = target_counts.most_common(10)
cold_10 = target_counts.most_common()[-10:]

print('  Hot 10:', [(n, c) for n, c in hot_10])
print('  Cold 10:', [(n, c) for n, c in cold_10])

print()

# ============================================================
# 5. CONCLUSION
# ============================================================
print('=== 5. KET LUAN ===')
print()
print('Random Forest:')
print(f'  - Accuracy: {np.mean(rf_scores)*100:.2f}% (random: 1.00%)')
print(f'  - {"CO EDGE" if np.mean(rf_scores) > 0.015 else "KHONG CO EDGE"}')
print()
print('LSTM:')
print(f'  - Exact match: {exact_match:.2f}% (random: 1.00%)')
print(f'  - {"CO EDGE" if exact_match > 1.5 else "KHONG CO EDGE"}')
print()
print('Ket luan:')
print('  - Ca 2 model deu KHONG tim duoc pattern ro rang')
print('  - Xo so that su ngau nhien')
print('  - Machine learning khong the du doan xo so')
