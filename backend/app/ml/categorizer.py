"""
Transaction Categorizer using TF-IDF + Random Forest

This model automatically categorizes transactions based on their description.
Uses TF-IDF vectorization with bigrams for feature extraction and a Random Forest
classifier with balanced class weights for robust multi-class classification.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
import re
import warnings

warnings.filterwarnings("ignore")


class TransactionCategorizer:
    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_path = os.path.join(self.model_dir, "categorizer_pipeline.joblib")
        self.pipeline = None
        self.categories = []
        self.is_trained = False
        self.accuracy = 0.0

    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize transaction descriptions."""
        text = text.lower().strip()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _build_pipeline(self) -> Pipeline:
        """Build the ML pipeline with TF-IDF and Random Forest."""
        return Pipeline([
            ('tfidf', TfidfVectorizer(
                preprocessor=self._preprocess_text,
                ngram_range=(1, 3),        # Unigrams, bigrams, and trigrams
                max_features=8000,
                min_df=1,
                max_df=0.95,
                sublinear_tf=True,         # Apply log normalization
                strip_accents='unicode',
                analyzer='word',
            )),
            ('classifier', RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                class_weight='balanced',   # Handle imbalanced categories
                random_state=42,
                n_jobs=None,               # Changed to prevent joblib hang
            ))
        ])

    def train(self, descriptions: list[str] = None, categories: list[str] = None):
        """
        Train the categorizer model.
        If no data provided, uses the seed training data.
        """
        if descriptions is None or categories is None:
            # Load seed data
            seed_path = os.path.join(
                os.path.dirname(__file__),
                "training_data",
                "seed_transactions.csv"
            )
            if not os.path.exists(seed_path):
                print("❌ No training data found!")
                return

            df = pd.read_csv(seed_path)
            descriptions = df['description'].tolist()
            categories = df['category'].tolist()

        self.categories = sorted(list(set(categories)))
        self.pipeline = self._build_pipeline()

        # Split for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            descriptions, categories, test_size=0.2, random_state=42, stratify=categories
        )

        # Train
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        self.accuracy = np.mean(np.array(y_pred) == np.array(y_test))

        # Cross-validation for more robust accuracy estimate
        cv_scores = cross_val_score(self.pipeline, descriptions, categories, cv=5, scoring='accuracy')

        print(f"✅ Categorizer trained!")
        print(f"   Test Accuracy: {self.accuracy:.2%}")
        print(f"   CV Accuracy:   {np.mean(cv_scores):.2%} (±{np.std(cv_scores):.2%})")
        print(f"   Categories:    {len(self.categories)}")

        # Retrain on full dataset for production use
        self.pipeline.fit(descriptions, categories)
        self.is_trained = True

        # Save model
        self._save_model()

    def predict(self, description: str) -> dict:
        """Predict category for a single transaction description."""
        if not self.is_trained:
            self.load_model()

        if not self.is_trained:
            return {"category": "Other", "confidence": 0.0, "probabilities": {}}

        category = self.pipeline.predict([description])[0]
        probabilities = self.pipeline.predict_proba([description])[0]
        confidence = float(max(probabilities))

        # Get top 3 predictions with probabilities
        top_indices = np.argsort(probabilities)[::-1][:3]
        top_predictions = {
            self.pipeline.classes_[i]: round(float(probabilities[i]), 4)
            for i in top_indices
        }

        return {
            "category": category,
            "confidence": round(confidence, 4),
            "top_predictions": top_predictions
        }

    def predict_batch(self, descriptions: list[str]) -> list[dict]:
        """Predict categories for multiple descriptions."""
        return [self.predict(desc) for desc in descriptions]

    def _save_model(self):
        """Save the trained model to disk."""
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump({
            'pipeline': self.pipeline,
            'categories': self.categories,
            'accuracy': self.accuracy,
        }, self.model_path)
        print(f"💾 Model saved to {self.model_path}")

    def load_model(self):
        """Load a previously trained model from disk."""
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.pipeline = data['pipeline']
            self.categories = data['categories']
            self.accuracy = data['accuracy']
            self.is_trained = True
            print(f"📦 Categorizer model loaded (accuracy: {self.accuracy:.2%})")
        else:
            print("⚠️ No saved model found. Training from seed data...")
            self.train()

    def retrain_with_feedback(self, new_descriptions: list[str], new_categories: list[str]):
        """
        Retrain the model incorporating user feedback/corrections.
        Combines seed data with user-corrected data for improved accuracy.
        """
        # Load seed data
        seed_path = os.path.join(
            os.path.dirname(__file__),
            "training_data",
            "seed_transactions.csv"
        )
        df = pd.read_csv(seed_path)
        all_descriptions = df['description'].tolist() + new_descriptions
        all_categories = df['category'].tolist() + new_categories

        self.train(all_descriptions, all_categories)
        print(f"🔄 Model retrained with {len(new_descriptions)} new examples")


# Global instance
categorizer = TransactionCategorizer()
# Reload trigger node
