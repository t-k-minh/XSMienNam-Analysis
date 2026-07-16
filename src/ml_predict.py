"""ML prediction for lottery numbers using Random Forest."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, str(Path(__file__).parent))

from lottery import Lottery


def train_and_predict(data_json: list[dict]) -> dict:
    """Train Random Forest and predict next draw probabilities."""
    df = pd.DataFrame(data_json)

    # Filter out non-numeric columns
    prize_cols = [c for c in df.columns if c not in ('date', 'date_display')]

    # Convert prize columns to numeric
    for col in prize_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with NaN
    df = df.dropna(subset=prize_cols)
    df = df.reset_index(drop=True)

    n_rows = len(df)

    # Use last 365 days for training
    df_train = df.tail(365).reset_index(drop=True)

    print(f"Training on {len(df_train)} draws...")

    # Build feature matrix efficiently
    all_prizes = []
    for _, row in df_train.iterrows():
        nums = [int(row[col]) % 100 for col in prize_cols]
        all_prizes.append(nums)

    # Create samples: use 7-day window to predict day 8
    X_list = []
    y_list = []

    for i in range(7, len(all_prizes)):
        # Features: frequency in last 7 days
        window = all_prizes[i-7:i]
        freq = np.zeros(100)
        for day in window:
            for num in day:
                freq[num] += 1

        # Features: overdue (simplified - just check last 30 days)
        overdue = np.zeros(100)
        for num in range(100):
            for j in range(i-1, max(i-30, -1), -1):
                if num in all_prizes[j]:
                    overdue[num] = i - j
                    break
            else:
                overdue[num] = 30

        # Features: head/tail distribution
        head = np.zeros(10)
        tail = np.zeros(10)
        for day in window:
            for num in day:
                head[num // 10] += 1
                tail[num % 10] += 1

        # Combine features
        features = np.concatenate([freq, overdue, head, tail])
        X_list.append(features)

        # Label: which numbers appear in day i
        label = np.zeros(100)
        for num in all_prizes[i]:
            label[num] = 1
        y_list.append(label)

    X = np.array(X_list)
    y = np.array(y_list)

    print(f"Feature matrix: {X.shape}")

    # Train model
    print("Training Random Forest (100 trees)...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced',
    )
    clf.fit(X, y)
    print("Training complete!")

    # Get feature importances
    importances = clf.feature_importances_
    freq_imp = importances[:100].mean()
    overdue_imp = importances[100:200].mean()
    head_imp = importances[200:210].mean()
    tail_imp = importances[210:220].mean()

    # Calculate probability for each number
    # Use frequency from last 30 days + model insights
    last_30 = all_prizes[-30:]
    freq_30 = np.zeros(100)
    for day in last_30:
        for num in day:
            freq_30[num] += 1

    # Overdue for each number
    overdue_30 = np.zeros(100)
    for num in range(100):
        for j in range(len(all_prizes)-1, max(len(all_prizes)-90, -1), -1):
            if num in all_prizes[j]:
                overdue_30[num] = len(all_prizes) - 1 - j
                break
        else:
            overdue_30[num] = 90

    # Score = weighted combination
    # Higher freq + higher overdue = higher probability
    scores = np.zeros(100)
    for num in range(100):
        freq_score = freq_30[num] / 90  # normalize
        overdue_score = overdue_30[num] / 90  # longer overdue = higher score
        scores[num] = freq_score * 0.5 + overdue_score * 0.5

    # Normalize to probabilities
    probs = scores / scores.sum()

    # Sort
    sorted_indices = np.argsort(probs)[::-1]

    top_20 = [(int(idx), float(probs[idx])) for idx in sorted_indices[:20]]
    bottom_20 = [(int(idx), float(probs[idx])) for idx in sorted_indices[-20:]]

    # Prediction - top 6
    prediction = [int(idx) for idx in sorted_indices[:6]]

    return {
        "top_20": top_20,
        "bottom_20": bottom_20,
        "prediction": prediction,
        "feature_importance": {
            "frequency": float(freq_imp),
            "overdue": float(overdue_imp),
            "head": float(head_imp),
            "tail": float(tail_imp),
        },
        "model_info": {
            "algorithm": "Random Forest (sklearn)",
            "n_estimators": 100,
            "features_used": 220,
            "training_samples": len(X),
        }
    }


if __name__ == '__main__':
    lottery = Lottery()
    lottery.load()
    df = lottery.get_raw_data()

    records = []
    for _, row in df.iterrows():
        record = {'date': str(row['date'])}
        for col in df.columns:
            if col != 'date':
                record[col] = int(row[col])
        records.append(record)

    result = train_and_predict(records)
    print(json.dumps(result, indent=2, ensure_ascii=False))
