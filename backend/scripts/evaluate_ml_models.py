"""
Evaluate Finance Tracker ML models on local MongoDB transaction history.

Outputs:
- Spending predictor backtest metrics (time-based walk-forward evaluation)
- Anomaly detector benchmark metrics (normal holdout + synthetic anomalies)
"""

from __future__ import annotations

from datetime import datetime, timedelta
import random
import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    r2_score,
)

from app.ml.predictor import SpendingPredictor
from app.ml.anomaly import AnomalyDetector


RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


def _parse_date(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now()


def fetch_expense_transactions(db) -> list[dict]:
    docs = list(db.transactions.find({"type": "expense"}).sort("date", 1))
    txns = []
    for d in docs:
        txns.append(
            {
                "date": _parse_date(d.get("date")),
                "amount": float(d.get("amount", 0.0)),
                "type": "expense",
                "category": d.get("category", "Other"),
                "description": d.get("description", ""),
            }
        )
    return txns


def build_daily_expense_dataframe(expense_txns: list[dict]) -> pd.DataFrame:
    if not expense_txns:
        return pd.DataFrame(columns=["date", "total"])

    df = pd.DataFrame(expense_txns)
    df["date_only"] = pd.to_datetime(df["date"]).dt.date
    daily = (
        df.groupby("date_only", as_index=False)["amount"]
        .sum()
        .rename(columns={"date_only": "date", "amount": "total"})
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)
    return daily


def evaluate_spending_predictor(daily_df: pd.DataFrame) -> dict:
    # Need enough days for repeated walk-forward training and testing.
    if len(daily_df) < 16:
        return {"error": f"Need >= 16 daily expense points, found {len(daily_df)}"}

    y_true = []
    y_pred = []

    # Walk-forward: train on [0...i-1], predict day i.
    for i in range(14, len(daily_df)):
        train_slice = daily_df.iloc[:i]
        target_row = daily_df.iloc[i]

        train_transactions = [
            {
                "date": row.date.to_pydatetime(),
                "amount": float(row.total),
                "type": "expense",
                "category": "Other",
            }
            for row in train_slice.itertuples(index=False)
        ]

        predictor = SpendingPredictor()
        predictor.train(train_transactions)
        if not predictor.is_trained or predictor.model is None:
            continue

        X_test = predictor._create_features([target_row["date"].to_pydatetime()])
        pred = float(predictor.model.predict(X_test)[0])
        pred = max(0.0, pred)

        y_true.append(float(target_row["total"]))
        y_pred.append(pred)

    if not y_true:
        return {"error": "Backtest produced no valid prediction points"}

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    mae = mean_absolute_error(y_true_arr, y_pred_arr)
    rmse = np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))
    r2 = r2_score(y_true_arr, y_pred_arr) if len(y_true_arr) > 1 else 0.0

    non_zero_mask = y_true_arr != 0
    if np.any(non_zero_mask):
        mape = float(
            np.mean(
                np.abs((y_true_arr[non_zero_mask] - y_pred_arr[non_zero_mask]) / y_true_arr[non_zero_mask])
            )
        )
    else:
        mape = 0.0

    within_20 = np.mean(np.abs(y_pred_arr - y_true_arr) <= 0.2 * np.maximum(y_true_arr, 1e-9))
    within_30 = np.mean(np.abs(y_pred_arr - y_true_arr) <= 0.3 * np.maximum(y_true_arr, 1e-9))

    return {
        "evaluation_points": int(len(y_true_arr)),
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "mape": float(mape),
        "accuracy_within_20pct": float(within_20),
        "accuracy_within_30pct": float(within_30),
    }


def _generate_synthetic_anomalies(reference_txns: list[dict], n_samples: int) -> list[dict]:
    amounts = np.array([float(t.get("amount", 0.0)) for t in reference_txns if t.get("amount", 0) > 0], dtype=float)
    categories = [t.get("category", "Other") for t in reference_txns] or ["Other"]

    if len(amounts) == 0:
        amounts = np.array([100.0], dtype=float)

    mean_amt = float(np.mean(amounts))
    std_amt = float(np.std(amounts))
    p95_amt = float(np.percentile(amounts, 95))
    high_base = max(mean_amt + 4 * max(std_amt, 1.0), p95_amt * 2, 100.0)

    anomalies = []
    now = datetime.now()
    weird_hours = [0, 1, 2, 3, 4, 23]

    for _ in range(n_samples):
        days_back = random.randint(0, 90)
        hour = random.choice(weird_hours)
        minute = random.randint(0, 59)
        dt = (now - timedelta(days=days_back)).replace(hour=hour, minute=minute, second=0, microsecond=0)

        amount = float(np.random.uniform(high_base, high_base * 1.8))
        anomalies.append(
            {
                "date": dt,
                "amount": amount,
                "type": "expense",
                "category": random.choice(categories),
                "description": "synthetic_high_value_outlier",
            }
        )

    return anomalies


def evaluate_anomaly_detector(expense_txns: list[dict]) -> dict:
    if len(expense_txns) < 25:
        return {"error": f"Need >= 25 expense transactions, found {len(expense_txns)}"}

    split_idx = max(20, int(len(expense_txns) * 0.7))
    if split_idx >= len(expense_txns):
        split_idx = len(expense_txns) - 1

    train_txns = expense_txns[:split_idx]
    holdout_normal = expense_txns[split_idx:]

    detector = AnomalyDetector()
    detector.train(train_txns)
    if not detector.is_trained or detector.model is None:
        return {"error": "Anomaly detector did not train successfully"}

    n_synth = max(10, len(holdout_normal))
    synth_anomalies = _generate_synthetic_anomalies(train_txns, n_synth)

    eval_set = holdout_normal + synth_anomalies
    y_true = np.array([0] * len(holdout_normal) + [1] * len(synth_anomalies))

    X = detector._extract_features(eval_set)
    X_scaled = detector.scaler.transform(X)
    pred_raw = detector.model.predict(X_scaled)  # -1 anomaly, 1 normal
    y_pred = np.array([1 if p == -1 else 0 for p in pred_raw])

    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )

    normal_mask = y_true == 0
    synth_mask = y_true == 1
    false_positive_rate = float(np.mean(y_pred[normal_mask] == 1)) if np.any(normal_mask) else 0.0
    synthetic_detection_rate = float(np.mean(y_pred[synth_mask] == 1)) if np.any(synth_mask) else 0.0

    return {
        "train_samples": int(len(train_txns)),
        "holdout_normal_samples": int(len(holdout_normal)),
        "synthetic_anomaly_samples": int(len(synth_anomalies)),
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate_on_normal_holdout": false_positive_rate,
        "detection_rate_on_synthetic_anomalies": synthetic_detection_rate,
    }


def main():
    client = MongoClient("mongodb://localhost:27017")
    db = client["finance_tracker"]

    expenses = fetch_expense_transactions(db)
    daily = build_daily_expense_dataframe(expenses)

    predictor_metrics = evaluate_spending_predictor(daily)
    anomaly_metrics = evaluate_anomaly_detector(expenses)

    print("=== Spending Predictor Metrics ===")
    for k, v in predictor_metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")

    print("\n=== Anomaly Detector Metrics ===")
    for k, v in anomaly_metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
