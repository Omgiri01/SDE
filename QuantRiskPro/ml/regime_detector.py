"""
regime_detector.py
------------------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro ML Module 2/5: Market Regime Detection

Model: Gaussian Hidden Markov Model (HMM)

Why HMM for regime detection:
  Financial markets alternate between hidden states (regimes):
    - State 0 (Bull):    high positive returns, low volatility
    - State 1 (Bear):    negative returns, high volatility, fat tails
    - State 2 (Sideways): near-zero returns, medium volatility
  
  HMM assumes:
    1. The current state is unobservable (hidden)
    2. The state follows a Markov chain (next state depends only on current)
    3. Each state emits observable returns/volatility drawn from a Gaussian
  
  The Baum-Welch algorithm (EM variant) fits the transition matrix A,
  emission parameters μ, Σ, and initial state distribution π.
  
  Viterbi decoding recovers the most-probable state sequence given returns.

Features used:
  - 1-day log return
  - 5-day rolling volatility (annualized)
  These two together distinguish bull (high return, low vol) from
  bear (negative return, high vol) and sideways (low return, medium vol).
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


REGIME_NAMES = {0: "Bull 🟢", 1: "Bear 🔴", 2: "Sideways 🟡"}
REGIME_COLORS = {0: "#22c55e", 1: "#ef4444", 2: "#eab308"}


@dataclass
class RegimeState:
    current_regime: int
    regime_name: str
    regime_color: str
    probability: float
    transition_matrix: list
    regime_history: list
    regime_stats: dict


class MarketRegimeDetector:
    """
    Gaussian HMM with 3 hidden states for market regime classification.
    
    Observables: [daily_return, rolling_5d_volatility]
    Hidden states: Bull (0), Bear (1), Sideways (2)
    """

    def __init__(self, n_states: int = 3, n_iter: int = 100):
        self.n_states = n_states
        self.n_iter = n_iter
        self.model = None
        self.is_fitted = False
        self._state_map = {}   # maps model state idx → regime label

    def _prepare_features(self, prices: np.ndarray) -> np.ndarray:
        """
        Build feature matrix from price series.
        Returns shape (n_days-5, 2): [log_return, rolling_vol]
        """
        log_returns = np.diff(np.log(prices))
        rolling_vol = np.array([
            log_returns[max(0, i-4):i+1].std() * np.sqrt(252)
            for i in range(len(log_returns))
        ])
        features = np.column_stack([log_returns, rolling_vol])
        return features.astype(np.float64)

    def fit(self, prices: np.ndarray) -> dict:
        """
        Fit the HMM on historical price series using Baum-Welch (EM).
        
        prices: 1D array of close prices (at least 100 days recommended)
        """
        try:
            from hmmlearn.hmm import GaussianHMM
        except ImportError:
            return self._fit_fallback(prices)

        features = self._prepare_features(prices)

        self.model = GaussianHMM(
            n_components=self.n_states,
            covariance_type="full",
            n_iter=self.n_iter,
            random_state=42,
        )
        self.model.fit(features)

        # Decode full sequence with Viterbi
        states = self.model.predict(features)

        # Assign regime labels by sorting states by mean return
        mean_returns = [
            features[states == s, 0].mean() if (states == s).any() else 0
            for s in range(self.n_states)
        ]
        sorted_states = np.argsort(mean_returns)[::-1]  # high return → bull
        self._state_map = {
            int(sorted_states[0]): 0,  # Bull
            int(sorted_states[1]): 2,  # Sideways (middle)
            int(sorted_states[2]): 1,  # Bear
        }
        if self.n_states == 2:
            self._state_map = {int(sorted_states[0]): 0, int(sorted_states[1]): 1}

        self.is_fitted = True

        regime_seq = [self._state_map.get(int(s), 2) for s in states]
        regime_counts = {REGIME_NAMES[r]: int(regime_seq.count(r)) for r in range(self.n_states)}

        return {
            "model": "Gaussian HMM (Baum-Welch EM)",
            "n_states": self.n_states,
            "n_iter": self.n_iter,
            "convergence_monitor": self.model.monitor_.converged,
            "log_likelihood": round(float(self.model.score(features)), 4),
            "regime_distribution": regime_counts,
            "transition_matrix": self.model.transmat_.round(4).tolist(),
        }

    def _fit_fallback(self, prices: np.ndarray) -> dict:
        """Fallback regime detection using return quantiles (no hmmlearn)."""
        log_returns = np.diff(np.log(prices))
        q33 = np.percentile(log_returns, 33)
        q67 = np.percentile(log_returns, 67)
        self._quantile_thresholds = (q33, q67)
        self.is_fitted = True
        self._use_fallback = True
        return {"model": "Quantile-based fallback (hmmlearn not installed)"}

    def predict_current(self, prices: np.ndarray) -> RegimeState:
        """
        Predict the current market regime from recent prices.
        Uses the last 60 days for context-aware Viterbi decoding.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() before predict_current()")

        features = self._prepare_features(prices[-60:] if len(prices) >= 60 else prices)

        if getattr(self, '_use_fallback', False):
            last_ret = features[-1, 0]
            q33, q67 = self._quantile_thresholds
            if last_ret > q67:
                raw_state, prob = 0, 0.75
            elif last_ret < q33:
                raw_state, prob = 1, 0.75
            else:
                raw_state, prob = 2, 0.65
        else:
            states = self.model.predict(features)
            raw_state = int(states[-1])
            # Get posterior probability of current state
            probs = self.model.predict_proba(features)
            prob = float(probs[-1, raw_state])

        regime_idx = self._state_map.get(raw_state, 2)
        regime_seq_raw = self.model.predict(features) if not getattr(self, '_use_fallback', False) else []
        regime_history = [self._state_map.get(int(s), 2) for s in regime_seq_raw]

        # Per-regime statistics from fitted emission parameters
        regime_stats = {}
        if not getattr(self, '_use_fallback', False):
            for model_s, regime_label in self._state_map.items():
                means = self.model.means_[model_s]
                regime_stats[REGIME_NAMES[regime_label]] = {
                    "mean_daily_return_pct": round(float(means[0]) * 100, 4),
                    "mean_annualized_vol_pct": round(float(means[1]) * 100, 2),
                }

        return RegimeState(
            current_regime=regime_idx,
            regime_name=REGIME_NAMES[regime_idx],
            regime_color=REGIME_COLORS[regime_idx],
            probability=round(prob, 4),
            transition_matrix=self.model.transmat_.round(4).tolist() if not getattr(self, '_use_fallback', False) else [],
            regime_history=regime_history[-30:],  # last 30 days
            regime_stats=regime_stats,
        )
