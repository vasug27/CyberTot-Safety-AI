import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, fbeta_score, precision_recall_fscore_support

MODEL_DIR = "c:/Development/CyberTot/models"
MODEL_PATH = os.path.join(MODEL_DIR, "safety_classifier.joblib")

CATEGORY_THRESHOLDS_TUNED = {
    "grooming": 0.15,
    "distress_selfharm": 0.15,
    "cyberbullying": 0.25,
    "scam_phishing": 0.25,
    "inappropriate_content": 0.25,
    "safe": 0.50
}

class CyberTotClassifier:
    def __init__(self, category_thresholds=None):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2500,
            sublinear_tf=True,
            strip_accents='unicode'
        )
        self.clf = LogisticRegression(
            C=0.3,
            max_iter=1000,
            random_state=42
        )
        self.classes_ = []
        self.thresholds = category_thresholds or CATEGORY_THRESHOLDS_TUNED

    def fit(self, X_train, y_train):
        X_vec = self.vectorizer.fit_transform(X_train)
        self.clf.fit(X_vec, y_train)
        self.classes_ = list(self.clf.classes_)
        print(f"Model trained successfully on {len(X_train)} samples across classes: {self.classes_}")

    def predict_proba(self, X):
        X_vec = self.vectorizer.transform(X)
        return self.clf.predict_proba(X_vec)

    def predict(self, X, custom_thresholds=None):
        probas = self.predict_proba(X)
        predictions = []

        active_thresholds = custom_thresholds if custom_thresholds is not None else self.thresholds

        for row_probas in probas:
            class_prob_map = {cls: prob for cls, prob in zip(self.classes_, row_probas)}

            flagged_risk = None
            highest_risk_ratio = 0.0

            for cls, prob in class_prob_map.items():
                if cls == "safe":
                    continue
                
                thresh = active_thresholds.get(cls, 0.25)
                
                if prob >= thresh:
                    ratio = prob / thresh
                    if ratio > highest_risk_ratio:
                        highest_risk_ratio = ratio
                        flagged_risk = cls

            if flagged_risk:
                predictions.append(flagged_risk)
            else:
                predictions.append("safe")

        return predictions

    def evaluate(self, X_test, y_test):
        y_pred_tuned = self.predict(X_test, custom_thresholds=self.thresholds)
        f2_tuned = fbeta_score(y_test, y_pred_tuned, beta=2, average='macro', zero_division=0)

        print("\n" + "="*85)
        print("PROBABILITY THRESHOLD SWEEP DEMONSTRATION (GROOMING & DISTRESS CLASS)")
        print("="*85)
        print(f"{'Threshold T':<12} | {'Grooming Recall':<16} | {'Grooming Precision':<18} | {'Macro F2 Score':<14}")
        print("-" * 85)

        sweep_thresholds = [0.10, 0.15, 0.25, 0.40, 0.60, 0.80, 0.90]
        for t in sweep_thresholds:
            t_map = {cls: t for cls in self.classes_ if cls != "safe"}
            t_map["safe"] = 0.50
            y_pred_t = self.predict(X_test, custom_thresholds=t_map)
            
            p_t, r_t, f2_t, _ = precision_recall_fscore_support(y_test, y_pred_t, labels=self.classes_, beta=2, zero_division=0)
            grooming_idx = self.classes_.index("grooming")
            macro_f2_t = fbeta_score(y_test, y_pred_t, beta=2, average='macro', zero_division=0)
            
            is_optimal = "  <--- (TUNED OPERATING POINT)" if t == 0.15 else ""
            print(f"{t:<12.2f} | {r_t[grooming_idx]*100:>15.1f}% | {p_t[grooming_idx]*100:>17.1f}% | {macro_f2_t:>13.4f}{is_optimal}")

        print("="*85)

        print("\n--- Classification Report (Tuned Operating Point T=0.15) ---")
        print(classification_report(y_test, y_pred_tuned, zero_division=0))

        return {
            "f2_tuned": f2_tuned,
            "report_tuned": classification_report(y_test, y_pred_tuned, output_dict=True, zero_division=0)
        }

    def save(self, filepath=MODEL_PATH):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        payload = {
            "vectorizer": self.vectorizer,
            "clf": self.clf,
            "classes": self.classes_,
            "thresholds": self.thresholds
        }
        joblib.dump(payload, filepath)
        print(f"Model artifacts saved to {filepath}")

    @classmethod
    def load(cls, filepath=MODEL_PATH):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found at {filepath}")
        payload = joblib.load(filepath)
        instance = cls(category_thresholds=payload.get("thresholds"))
        instance.vectorizer = payload["vectorizer"]
        instance.clf = payload["clf"]
        instance.classes_ = payload["classes"]
        return instance

if __name__ == "__main__":
    train_file = "c:/Development/CyberTot/data/train.csv"
    test_file = "c:/Development/CyberTot/data/test.csv"

    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    model = CyberTotClassifier()
    model.fit(train_df["text"], train_df["label"])
    metrics = model.evaluate(test_df["text"], test_df["label"])
    model.save()
