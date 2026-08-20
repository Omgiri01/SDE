"""
lstm_forecaster.py
------------------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro ML Module 1/5: LSTM Price Forecasting

Architecture:
  Input:  sliding window of 30-day OHLCV + returns → shape (batch, 30, 5)
  Model:  2-layer stacked LSTM with dropout + LayerNorm → Linear head
  Output: next 5-day price forecast (multi-step)

Why LSTM over simple regression:
  - Stock prices are sequential: today's price depends on the past sequence
  - LSTM's gating mechanism (forget/input/output gates) selectively retains
    long-range dependencies (e.g., weekly patterns, earnings cycles)
  - Multi-step output forces the model to reason about trajectory, not just
    next-tick prediction

Training:
  - Loss: Huber loss (robust to outliers unlike MSE)
  - Optimizer: AdamW with cosine annealing LR schedule
  - Data: 252 trading days of OHLCV, normalized with MinMaxScaler
"""

import math
import numpy as np
from typing import Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEQ_LEN = 30       # 30 trading days lookback window
FORECAST_HORIZON = 5   # predict next 5 days
HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.2
FEATURES = 5       # open, high, low, close, volume (normalized)


class LSTMForecaster(nn.Module):
    """
    2-layer stacked LSTM for multi-step price forecasting.

    Architecture:
      LSTM(input=5, hidden=128, layers=2, dropout=0.2)
      → LayerNorm(128)
      → Linear(128, 64)
      → GELU activation
      → Linear(64, forecast_horizon)
    """

    def __init__(
        self,
        input_dim: int = FEATURES,
        hidden_dim: int = HIDDEN_DIM,
        num_layers: int = NUM_LAYERS,
        forecast_horizon: int = FORECAST_HORIZON,
        dropout: float = DROPOUT,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.forecast_horizon = forecast_horizon

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, forecast_horizon),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch_size, seq_len, input_dim)
        returns: (batch_size, forecast_horizon)
        """
        # h0, c0 initialized to zeros by default
        lstm_out, _ = self.lstm(x)          # (B, seq_len, hidden_dim)
        last_hidden = lstm_out[:, -1, :]    # take last timestep
        normed = self.layer_norm(last_hidden)
        return self.head(normed)             # (B, forecast_horizon)


class PriceForecasterService:
    """
    End-to-end service: prepare data → train → predict → serve via API.
    Designed to be loaded once at FastAPI startup and queried per request.
    """

    def __init__(self):
        self.model: Optional[LSTMForecaster] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.close_scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_trained = False

    def _make_sequences(
        self, data: np.ndarray, seq_len: int = SEQ_LEN, horizon: int = FORECAST_HORIZON
    ):
        """
        Build (X, y) sliding window pairs from normalized OHLCV array.
        X shape: (n_samples, seq_len, n_features)
        y shape: (n_samples, horizon)  — normalized close prices
        """
        X, y = [], []
        for i in range(len(data) - seq_len - horizon + 1):
            X.append(data[i : i + seq_len])
            y.append(data[i + seq_len : i + seq_len + horizon, 3])  # col 3 = close
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    def train(self, ohlcv: np.ndarray, epochs: int = 50, lr: float = 1e-3) -> dict:
        """
        Train the LSTM on historical OHLCV data.

        ohlcv: numpy array shape (n_days, 5) — [open, high, low, close, volume]
        Returns training summary dict.
        """
        # Normalize features
        scaled = self.scaler.fit_transform(ohlcv)

        X, y = self._make_sequences(scaled)
        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
        val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=32)

        self.model = LSTMForecaster(input_dim=ohlcv.shape[1]).to(DEVICE)
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        # Huber loss — robust to outlier returns (earnings surprises, flash crashes)
        criterion = nn.HuberLoss(delta=0.1)

        train_losses, val_losses = [], []

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0.0
            for xb, yb in train_loader:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                optimizer.zero_grad()
                pred = self.model(xb)
                loss = criterion(pred, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                train_loss += loss.item()
            scheduler.step()

            # Validation
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for xb, yb in val_loader:
                    xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                    val_loss += criterion(self.model(xb), yb).item()

            train_losses.append(train_loss / max(len(train_loader), 1))
            val_losses.append(val_loss / max(len(val_loader), 1))

        self.is_trained = True
        return {
            "epochs": epochs,
            "final_train_loss": round(train_losses[-1], 6),
            "final_val_loss": round(val_losses[-1], 6),
            "device": str(DEVICE),
            "model_params": sum(p.numel() for p in self.model.parameters()),
        }

    def predict(self, ohlcv: np.ndarray) -> dict:
        """
        Predict next FORECAST_HORIZON days from the last SEQ_LEN rows of ohlcv.

        Returns dict with forecast prices and confidence bounds.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        # Use last SEQ_LEN rows
        window = ohlcv[-SEQ_LEN:]
        scaled = self.scaler.transform(window)
        x = torch.tensor(scaled[np.newaxis, :, :], dtype=torch.float32).to(DEVICE)

        self.model.eval()
        with torch.no_grad():
            pred_scaled = self.model(x).cpu().numpy()[0]  # (horizon,)

        # Inverse transform close prices
        dummy = np.zeros((FORECAST_HORIZON, ohlcv.shape[1]))
        dummy[:, 3] = pred_scaled  # col 3 = close
        pred_prices = self.scaler.inverse_transform(dummy)[:, 3]

        last_price = float(ohlcv[-1, 3])
        return {
            "model": "LSTM (2-layer, 128 hidden, Huber loss)",
            "last_known_price": round(last_price, 4),
            "forecast_horizon_days": FORECAST_HORIZON,
            "forecast_prices": [round(float(p), 4) for p in pred_prices],
            "forecast_returns_pct": [
                round((float(pred_prices[i]) / last_price - 1) * 100, 4)
                for i in range(FORECAST_HORIZON)
            ],
            "device": str(DEVICE),
        }


def generate_synthetic_ohlcv(n_days: int = 400, seed: int = 42) -> np.ndarray:
    """
    Generate realistic OHLCV data using correlated GBM for training without Polygon.io.
    Used in demo mode to train the LSTM without real market data.
    """
    rng = np.random.default_rng(seed)
    prices = [150.0]
    mu, sigma = 0.08 / 252, 0.02
    for _ in range(n_days - 1):
        dW = rng.normal(0, 1)
        prices.append(prices[-1] * math.exp((mu - 0.5 * sigma**2) + sigma * dW))

    data = []
    for i, close in enumerate(prices):
        noise = rng.uniform(0.995, 1.005)
        open_ = close * rng.uniform(0.99, 1.01)
        high = close * rng.uniform(1.0, 1.015)
        low = close * rng.uniform(0.985, 1.0)
        vol = rng.integers(5_000_000, 30_000_000)
        data.append([open_, high, low, close * noise, vol])

    return np.array(data, dtype=np.float64)
