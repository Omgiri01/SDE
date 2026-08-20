"""
anomaly_detector.py
-------------------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro ML Module 3/5: Real-Time Anomaly Detection

Model: Isolation Forest (sklearn)

Why Isolation Forest:
  Flash crashes, pump-and-dump schemes, and fat-tail events share a property:
  they are easy to isolate with fewer random splits than normal observations.

  Algorithm:
    1. Randomly select a feature (e.g., return or volume)
    2. Randomly select a split value between min and max
    3. Repeat until the point is isolated
    Anomalies are isolated in fewer steps → shorter path length → lower score

  Benefits over z-score / 3-sigma rule:
    - Non-parametric (no Gaussian assumption)
    - Handles multivariate features jointly (return AND volume AND spread)
    - Contamination parameter controls false positive rate explicitly
    - O(n log n) — fast enough to run on each tick in production

Features:
  [log_return, rolling_vol_5d, volume_z_score, price_range_pct]
  Combining return + volume detects coordinated price manipulation that
  single-feature detectors miss (e.g., volume spike before crash).
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_score: float          # lower = more anomalous (-1 to 0)
    anomaly_probability: float    # 0 to 1 (1 = definitely anomalous)
    triggered_features: list      # which features drove the anomaly
    severity: str                 # "normal" | "warning" | "critical"


class AnomalyDetector:
    """
    Isolation Forest for real-time price anomaly detection.
    Trained on historical OHLCV bars, detects runtime anomalies on new ticks.
    """

    def __init__(self, contamination: float = 0.02, n_estimators: int = 200):
        """
        contamination: expected fraction of anomalies in training data (2%)
        n_estimators: number of isolation trees (more = more stable)
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = ["log_return", "rolling_vol_5d", "volume_zscore", "price_range_pct"]

    def _build_features(self, ohlcv: np.ndarray) -> np.ndarray:
        """
        Build anomaly detection feature matrix from OHLCV array.
        ohlcv: (n, 5) → [open, high, low, close, volume]
        Returns: (n-5, 4) feature matrix
        """
        opens = ohlcv[:, 0]
        highs = ohlcv[:, 1]
        lows = ohlcv[:, 2]
        closes = ohlcv[:, 3]
        volumes = ohlcv[:, 4]

        log_returns = np.diff(np.log(closes))
        n = len(log_returns)

        # 5-day rolling volatility (annualized)
        rolling_vol = np.array([
            log_returns[max(0, i-4):i+1].std() * np.sqrt(252)
            for i in range(n)
        ])

        # Volume z-score (deviation from 20-day mean)
        vol_z = np.zeros(n)
        for i in range(n):
            window = volumes[max(0, i-19):i+1]
            if window.std() > 0:
                vol_z[i] = (volumes[i+1] - window.mean()) / window.std()

        # Daily price range as % of open (intraday volatility proxy)
        price_range = (highs[1:] - lows[1:]) / opens[1:] * 100

        features = np.column_stack([log_returns, rolling_vol, vol_z, price_range])
        return features.astype(np.float64)

    def fit(self, ohlcv: np.ndarray) -> dict:
        """
        Train Isolation Forest on historical OHLCV data.
        ohlcv: shape (n_days, 5)
        """
        features = self._build_features(ohlcv)
        features_scaled = self.scaler.fit_transform(features)
        self.model.fit(features_scaled)
        self.is_fitted = True

        # Report how many anomalies were found in training data
        preds = self.model.predict(features_scaled)
        n_anomalies = int((preds == -1).sum())

        return {
            "model": "Isolation Forest",
            "n_estimators": self.model.n_estimators,
            "contamination": self.model.contamination,
            "n_training_samples": len(features),
            "n_anomalies_in_training": n_anomalies,
            "anomaly_rate_pct": round(n_anomalies / len(features) * 100, 2),
            "features": self.feature_names,
        }

    def detect(self, ohlcv_window: np.ndarray) -> AnomalyResult:
        """
        Detect if the latest data point is anomalous.
        ohlcv_window: at least 21 rows of OHLCV for feature computation.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() first.")

        features = self._build_features(ohlcv_window)
        if len(features) == 0:
            return AnomalyResult(False, 0.0, 0.0, [], "normal")

        latest = features[-1:, :]
        latest_scaled = self.scaler.transform(latest)

        prediction = self.model.predict(latest_scaled)[0]  # 1=normal, -1=anomaly
        score = float(self.model.score_samples(latest_scaled)[0])  # lower = worse

        # Convert score to probability (score in [-0.5, 0.5] approx)
        anomaly_prob = max(0.0, min(1.0, -score * 2))

        is_anomaly = prediction == -1

        # Identify which features are extreme (|z| > 2.5)
        z_scores = latest_scaled[0]
        triggered = [
            self.feature_names[i]
            for i, z in enumerate(z_scores)
            if abs(z) > 2.5
        ]

        if anomaly_prob > 0.7:
            severity = "critical"
        elif anomaly_prob > 0.4 or is_anomaly:
            severity = "warning"
        else:
            severity = "normal"

        return AnomalyResult(
            is_anomaly=bool(is_anomaly),
            anomaly_score=round(score, 4),
            anomaly_probability=round(anomaly_prob, 4),
            triggered_features=triggered,
            severity=severity,
        )
