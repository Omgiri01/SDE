import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import time
from ml.ml_routes import _sync_train

print("Starting benchmark of _sync_train(4 tickers: AAPL, TSLA, MSFT, NVDA)...", flush=True)
t0 = time.time()
res = _sync_train(["AAPL", "TSLA", "MSFT", "NVDA"])
elapsed = time.time() - t0

print(f"\n============================================================", flush=True)
print(f"  TOTAL TRAINING TIME: {elapsed:.2f} seconds ({elapsed/4:.2f}s per ticker)", flush=True)
print(f"============================================================", flush=True)
for t in ["AAPL", "TSLA", "MSFT", "NVDA"]:
    lstm_loss = res[t]["lstm"]["final_train_loss"]
    hmm_conv = res[t]["regime_detector"].get("convergence_monitor", True)
    anom_cnt = res[t]["anomaly_detector"]["n_anomalies_in_training"]
    print(f"  [{t}] LSTM Loss: {lstm_loss} | HMM Converged: {hmm_conv} | IsoForest Anomalies: {anom_cnt}", flush=True)
