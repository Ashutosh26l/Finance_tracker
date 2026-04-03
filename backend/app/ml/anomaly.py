"""
Anomaly Detection using Isolation Forest

Detects unusual transactions based on amount, timing, and category patterns.
Uses Isolation Forest — an unsupervised algorithm that isolates anomalies
instead of profiling normal observations.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.min_data_points = 20
        self.contamination = 0.08  # Expect ~8% anomalies

    def _extract_features(self, transactions: list[dict]) -> np.ndarray:
        """Extract numerical features from transactions for anomaly detection."""
        features = []
        for txn in transactions:
            date = txn.get('date', datetime.now())
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))

            features.append([
                txn.get('amount', 0),
                date.hour if hasattr(date, 'hour') else 12,
                date.weekday() if hasattr(date, 'weekday') else 0,
                date.day if hasattr(date, 'day') else 15,
                1 if (hasattr(date, 'weekday') and date.weekday() >= 5) else 0,
            ])

        return np.array(features)

    def train(self, transactions: list[dict]):
        """Train the anomaly detector on historical transactions."""
        expense_txns = [t for t in transactions if t.get('type') == 'expense']

        if len(expense_txns) < self.min_data_points:
            print(f"⚠️ Need at least {self.min_data_points} transactions for anomaly detection")
            self.is_trained = False
            return

        X = self._extract_features(expense_txns)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            max_samples='auto',
            random_state=42,
            # Single worker avoids joblib multiprocessing issues on some Windows setups.
            n_jobs=1,
        )
        self.model.fit(X_scaled)
        self.is_trained = True

        # Count anomalies in training data
        predictions = self.model.predict(X_scaled)
        n_anomalies = np.sum(predictions == -1)
        print(f"✅ Anomaly detector trained ({n_anomalies}/{len(expense_txns)} anomalies in training data)")

    def detect(self, transactions: list[dict]) -> list[dict]:
        """
        Detect anomalies in a list of transactions.

        Returns list of anomalous transactions with scores and reasons.
        """
        if not transactions:
            return []

        expense_txns = [t for t in transactions if t.get('type') == 'expense']

        if not expense_txns:
            return []

        # If not trained, train on the provided transactions
        if not self.is_trained:
            if len(expense_txns) >= self.min_data_points:
                self.train(transactions)
            else:
                # Fallback: use statistical method (Z-score on amounts)
                return self._statistical_detection(expense_txns)

        X = self._extract_features(expense_txns)
        X_scaled = self.scaler.transform(X)

        # Predict: -1 = anomaly, 1 = normal
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)

        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                txn = expense_txns[i]
                reason = self._generate_reason(txn, expense_txns, score)
                anomalies.append({
                    "id": str(txn.get('_id', txn.get('id', ''))),
                    "description": txn.get('description', ''),
                    "amount": txn.get('amount', 0),
                    "category": txn.get('category', 'Other'),
                    "date": txn.get('date', datetime.now()),
                    "anomaly_score": round(float(score), 4),
                    "reason": reason,
                })

        # Sort by anomaly score (most anomalous first)
        anomalies.sort(key=lambda x: x['anomaly_score'])

        return anomalies

    def _statistical_detection(self, transactions: list[dict]) -> list[dict]:
        """Fallback statistical anomaly detection using Z-scores."""
        if len(transactions) < 3:
            return []

        amounts = [t.get('amount', 0) for t in transactions]
        mean_amount = np.mean(amounts)
        std_amount = np.std(amounts)

        if std_amount == 0:
            return []

        anomalies = []
        for txn in transactions:
            z_score = (txn.get('amount', 0) - mean_amount) / std_amount
            if abs(z_score) > 2.0:  # More than 2 standard deviations
                anomalies.append({
                    "id": str(txn.get('_id', txn.get('id', ''))),
                    "description": txn.get('description', ''),
                    "amount": txn.get('amount', 0),
                    "category": txn.get('category', 'Other'),
                    "date": txn.get('date', datetime.now()),
                    "anomaly_score": round(float(-abs(z_score)), 4),
                    "reason": f"Amount is {abs(z_score):.1f}x standard deviations from your average spending of ${mean_amount:.2f}",
                })

        return anomalies

    def _generate_reason(self, txn: dict, all_txns: list[dict], score: float) -> str:
        """Generate a human-readable reason for why this transaction is anomalous."""
        amount = txn.get('amount', 0)
        category = txn.get('category', 'Other')

        # Calculate category average
        cat_txns = [t for t in all_txns if t.get('category') == category]
        cat_avg = np.mean([t.get('amount', 0) for t in cat_txns]) if cat_txns else 0
        overall_avg = np.mean([t.get('amount', 0) for t in all_txns])

        reasons = []

        if cat_avg > 0 and amount > cat_avg * 2:
            reasons.append(f"Amount (${amount:.2f}) is {amount/cat_avg:.1f}x higher than your average {category} spending (${cat_avg:.2f})")
        elif amount > overall_avg * 3:
            reasons.append(f"Amount (${amount:.2f}) is {amount/overall_avg:.1f}x higher than your overall average spending (${overall_avg:.2f})")

        date = txn.get('date', datetime.now())
        if hasattr(date, 'hour'):
            if date.hour < 6 or date.hour > 23:
                reasons.append(f"Unusual transaction time ({date.strftime('%I:%M %p')})")

        if hasattr(date, 'weekday') and date.weekday() >= 5:
            if cat_txns:
                weekend_txns = [t for t in cat_txns
                                if hasattr(t.get('date'), 'weekday') and t['date'].weekday() >= 5]
                if len(weekend_txns) < len(cat_txns) * 0.2:
                    reasons.append("Unusual weekend transaction for this category")

        if not reasons:
            reasons.append(f"Unusual spending pattern detected (anomaly score: {score:.3f})")

        return "; ".join(reasons)

    def check_single(self, transaction: dict, historical: list[dict]) -> dict:
        """Check if a single transaction is anomalous against historical data."""
        if not self.is_trained and len(historical) >= self.min_data_points:
            self.train(historical)

        if self.is_trained:
            X = self._extract_features([transaction])
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]
            score = self.model.decision_function(X_scaled)[0]

            is_anomaly = prediction == -1
            reason = ""
            if is_anomaly:
                reason = self._generate_reason(transaction, historical, score)

            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": round(float(score), 4),
                "reason": reason,
            }
        else:
            # Use statistical method
            amounts = [t.get('amount', 0) for t in historical if t.get('type') == 'expense']
            if amounts:
                mean_amount = np.mean(amounts)
                std_amount = np.std(amounts) or 1
                z_score = (transaction.get('amount', 0) - mean_amount) / std_amount
                return {
                    "is_anomaly": abs(z_score) > 2.0,
                    "anomaly_score": round(float(-abs(z_score)), 4),
                    "reason": f"Amount is {abs(z_score):.1f}x std devs from average" if abs(z_score) > 2.0 else "",
                }

            return {"is_anomaly": False, "anomaly_score": 0.0, "reason": ""}


# Global instance
anomaly_detector = AnomalyDetector()
