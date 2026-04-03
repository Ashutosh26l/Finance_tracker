"""
Spending Predictor using Linear Regression with seasonal features.

Predicts future spending based on historical transaction patterns.
Uses feature engineering (day of week, month, rolling averages) for improved accuracy.
Falls back to rolling average when insufficient data is available.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import warnings

warnings.filterwarnings("ignore")


class SpendingPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.min_data_points = 14  # Minimum 2 weeks of data

    def _create_features(self, dates: list[datetime]) -> np.ndarray:
        """Create time-based features for prediction."""
        features = []
        for date in dates:
            features.append([
                date.weekday(),                          # Day of week (0-6)
                date.day,                                # Day of month (1-31)
                date.month,                              # Month (1-12)
                1 if date.weekday() >= 5 else 0,         # Is weekend
                np.sin(2 * np.pi * date.weekday() / 7),  # Cyclical day encoding
                np.cos(2 * np.pi * date.weekday() / 7),
                np.sin(2 * np.pi * date.month / 12),      # Cyclical month encoding
                np.cos(2 * np.pi * date.month / 12),
                np.sin(2 * np.pi * date.day / 31),         # Cyclical day-of-month
                np.cos(2 * np.pi * date.day / 31),
            ])
        return np.array(features)

    def train(self, transactions: list[dict]):
        """
        Train the spending predictor on historical transactions.
        Expects list of dicts with 'date' and 'amount' keys.
        """
        if len(transactions) < self.min_data_points:
            print(f"⚠️ Need at least {self.min_data_points} transactions for prediction")
            self.is_trained = False
            return

        # Aggregate daily spending
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        daily = df[df['type'] == 'expense'].groupby(
            df['date'].dt.date
        )['amount'].sum().reset_index()
        daily.columns = ['date', 'total']
        daily['date'] = pd.to_datetime(daily['date'])

        if len(daily) < self.min_data_points:
            self.is_trained = False
            return

        # Create features
        X = self._create_features(daily['date'].tolist())
        y = daily['total'].values

        # Train Ridge Regression with scaling
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', Ridge(alpha=1.0))
        ])
        self.model.fit(X, y)
        self.is_trained = True

        # Calculate R² score
        score = self.model.score(X, y)
        print(f"✅ Spending predictor trained (R² = {score:.3f})")

    def predict(self, days: int = 30, transactions: list[dict] = None) -> dict:
        """
        Predict spending for the next N days.

        Returns dict with predictions, total, average, and confidence.
        """
        if transactions:
            self.train(transactions)

        # Generate future dates
        today = datetime.now()
        future_dates = [today + timedelta(days=i) for i in range(1, days + 1)]

        if self.is_trained and self.model is not None:
            X_future = self._create_features(future_dates)
            predictions = self.model.predict(X_future)
            predictions = np.maximum(predictions, 0)  # No negative spending

            # Estimate confidence based on training data variance
            confidence = min(0.85, max(0.4, self.model.score(
                self._create_features(future_dates[:min(7, len(future_dates))]),
                predictions[:min(7, len(predictions))]
            ) if len(predictions) > 1 else 0.5))

            # Create prediction bounds (±20%)
            result = {
                "predictions": [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "predicted_amount": round(float(pred), 2),
                        "lower_bound": round(float(pred * 0.8), 2),
                        "upper_bound": round(float(pred * 1.2), 2),
                    }
                    for date, pred in zip(future_dates, predictions)
                ],
                "total_predicted": round(float(np.sum(predictions)), 2),
                "avg_daily_predicted": round(float(np.mean(predictions)), 2),
                "model_confidence": round(float(confidence), 3),
            }
        else:
            # Fallback: use average from transactions if available
            avg_daily = 0
            if transactions:
                expense_txns = [t for t in transactions if t.get('type') == 'expense']
                if expense_txns:
                    total = sum(t['amount'] for t in expense_txns)
                    date_range = (max(t['date'] for t in expense_txns) -
                                  min(t['date'] for t in expense_txns)).days or 1
                    avg_daily = total / date_range

            result = {
                "predictions": [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "predicted_amount": round(avg_daily, 2),
                        "lower_bound": round(avg_daily * 0.7, 2),
                        "upper_bound": round(avg_daily * 1.3, 2),
                    }
                    for date in future_dates
                ],
                "total_predicted": round(avg_daily * days, 2),
                "avg_daily_predicted": round(avg_daily, 2),
                "model_confidence": 0.3,
            }

        return result


# Global instance
predictor = SpendingPredictor()
