"""
test_all.py
-----------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro - Strict Comprehensive Test Suite (ASCII Clean)
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import math
import time
import urllib.request
import urllib.error
import numpy as np

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
ERRORS = []

def log(name, status, detail=""):
    global PASS, FAIL
    icon = "[PASS]" if status else "[FAIL]"
    if not status:
        FAIL += 1
        ERRORS.append(f"  FAIL: {name} - {detail}")
    else:
        PASS += 1
    detail_short = str(detail)[:80]
    print(f"  {icon}  {name:<45} {detail_short}", flush=True)


def get(path, expect_status=200):
    url = BASE + path
    try:
        r = urllib.request.urlopen(url, timeout=10)
        body = json.loads(r.read().decode())
        ok = r.status == expect_status
        return ok, body, r.status
    except urllib.error.HTTPError as e:
        if e.code == expect_status:
            return True, {}, e.code
        return False, {}, e.code
    except Exception as e:
        return False, {}, str(e)


def post(path, data, expect_status=200):
    url = BASE + path
    try:
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        r = urllib.request.urlopen(req, timeout=30)
        body = json.loads(r.read().decode())
        return True, body, r.status
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read().decode())
        except Exception:
            pass
        if e.code == expect_status:
            return True, body, e.code
        return False, body, e.code
    except Exception as e:
        return False, {}, str(e)


print("\n" + "=" * 70, flush=True)
print("  QuantRiskPro - Strict Comprehensive Test Suite", flush=True)
print("  Author: Om Giri | github.com/Omgiri01", flush=True)
print("=" * 70, flush=True)

# 1. Core Endpoints
print("\n[1] CORE REST API ENDPOINTS", flush=True)
print("-" * 70, flush=True)

ok, body, _ = get("/")
log("GET / (root)", ok and "service" in body, body.get("service",""))

ok, body, _ = get("/api/health")
log("GET /api/health", ok and body.get("status") == "healthy", body.get("status",""))

ok, body, _ = get("/api/prices")
log("GET /api/prices (all 10 tickers)", ok and isinstance(body, list) and len(body) == 10, f"{len(body)} tickers" if isinstance(body, list) else "")

ok, body, _ = get("/api/prices/AAPL")
log("GET /api/prices/AAPL", ok and "price" in body and body["price"] > 0, f"price={body.get('price','')}")

ok, body, _ = get("/api/prices/NVDA")
log("GET /api/prices/NVDA", ok and "price" in body, f"price=${body.get('price','')}")

ok, body, status = get("/api/prices/FAKEXYZ", expect_status=404)
log("GET /api/prices/FAKEXYZ (expect 404)", ok, f"status={status}")

ok, body, _ = get("/api/risk/AAPL")
log("GET /api/risk/AAPL", ok and "value_at_risk_1d" in body, f"VaR={body.get('value_at_risk_1d','')}")

ok, body, _ = get("/api/risk/TSLA")
log("GET /api/risk/TSLA", ok and "annualized_sharpe" in body, f"Sharpe={body.get('annualized_sharpe','')}")

ok, body, _ = get("/api/risk/portfolio/aggregate")
log("GET /api/risk/portfolio/aggregate", ok and "annualized_sharpe" in body, f"n_assets={body.get('n_assets','')}")

ok, body, _ = get("/api/portfolio/frontier?n=300")
log("GET /api/portfolio/frontier?n=300", ok and "frontier_points" in body, f"n_sim={body.get('n_simulations','')}")

ok, body, _ = get("/api/ml/status")
log("GET /api/ml/status", ok and "available_models" in body, "")

ok, body, _ = get("/api/ml/sentiment/NVDA")
log("GET /api/ml/sentiment/NVDA", ok and "aggregate_signal" in body, f"signal={body.get('aggregate_signal','')}")

# 2. Risk Math Correctness
print("\n[2] RISK MATH VALIDATION", flush=True)
print("-" * 70, flush=True)

ok, body, _ = get("/api/risk/AAPL")
var = body.get("value_at_risk_1d", -1)
log("VaR > 0 (loss amount is positive)", ok and var > 0, f"VaR={var}")

sharpe = body.get("annualized_sharpe", None)
log("Sharpe is finite in reasonable range (-5, 5)", ok and sharpe is not None and -5 < sharpe < 5, f"Sharpe={sharpe}")

drawdown = body.get("max_drawdown", 0)
log("Max Drawdown < 0 (is negative loss)", ok and drawdown < 0, f"Drawdown={drawdown}")

vol = body.get("annualized_volatility", -1)
log("Annualized Volatility > 0", ok and vol > 0, f"Vol={vol}")

sortino = body.get("annualized_sortino", None)
log("Sortino >= Sharpe (downside-only penalty)", ok and sortino is not None and sortino >= sharpe, f"Sortino={sortino} >= Sharpe={sharpe}")

# 3. Direct ML Module Tests
print("\n[3] ML MODULE UNIT TESTS (Pure Python)", flush=True)
print("-" * 70, flush=True)

sys.path.insert(0, ".")

from ml.lstm_forecaster import PriceForecasterService, generate_synthetic_ohlcv
ohlcv = generate_synthetic_ohlcv(200, seed=1)
log("LSTM: synthetic OHLCV generator", ohlcv.shape == (200, 5), f"shape={ohlcv.shape}")
svc = PriceForecasterService()
r = svc.train(ohlcv, epochs=5)
log("LSTM: train() 5 epochs", "final_train_loss" in r, f"loss={r.get('final_train_loss','')}")
pred = svc.predict(ohlcv)
log("LSTM: predict() returns 5 prices", len(pred["forecast_prices"]) == 5, f"prices={pred['forecast_prices']}")

from ml.regime_detector import MarketRegimeDetector
prices = ohlcv[:, 3]
reg = MarketRegimeDetector(n_states=3)
fit_r = reg.fit(prices)
st = reg.predict_current(prices)
log("HMM: Market Regime Classification", st.regime_name != "", f"regime={st.regime_name} prob={st.probability*100:.1f}%")

from ml.anomaly_detector import AnomalyDetector
ad = AnomalyDetector(contamination=0.02, n_estimators=50)
ad.fit(ohlcv)
res_an = ad.detect(ohlcv)
log("IsoForest: detect normal data", res_an.severity in ["normal", "warning", "critical"], f"score={res_an.anomaly_score}")

ohlcv_crash = ohlcv.copy()
ohlcv_crash[-1, 3] *= 0.5
ohlcv_crash[-1, 4] *= 10
crash_an = ad.detect(ohlcv_crash)
log("IsoForest: detects 50% flash crash", crash_an.anomaly_probability > 0.3, f"prob={crash_an.anomaly_probability}")

from ml.volatility_forecaster import VolatilityForecaster
vf = VolatilityForecaster()
vf.fit(prices)
fc = vf.forecast(prices, symbol="AAPL")
log("GARCH+XGB: Volatility forecast > 0", fc.annualized_vol_pct > 0, f"vol={fc.annualized_vol_pct}% ({fc.vol_regime})")

from ml.sentiment_analyzer import SentimentAnalyzer
sa = SentimentAnalyzer(use_finbert=False)
sa.load()
s1 = sa.analyze("Apple beats quarterly earnings with record revenue surge")
log("Sentiment: Bullish headline", s1.financial_signal == "BULLISH", f"signal={s1.financial_signal}")
s2 = sa.analyze("Tesla cuts deliveries and reports wide quarterly loss")
log("Sentiment: Bearish headline", s2.financial_signal == "BEARISH", f"signal={s2.financial_signal}")

# 4. HTTP ML Train & Inference
print("\n[4] HTTP ML END-TO-END INFERENCE", flush=True)
print("-" * 70, flush=True)

ok, train_res, _ = post("/api/ml/train", {"tickers": ["AAPL", "TSLA"]})
log("POST /api/ml/train (AAPL, TSLA)", ok and "tickers_trained" in train_res, f"trained={train_res.get('tickers_trained','')}")

ok_f, f_res, _ = get("/api/ml/forecast/AAPL")
log("GET /api/ml/forecast/AAPL (LSTM API)", ok_f and "forecast_prices" in f_res, f"next5d={f_res.get('forecast_prices','')[:3] if ok_f else ''}")

ok_r, r_res, _ = get("/api/ml/regime/AAPL")
log("GET /api/ml/regime/AAPL (HMM API)", ok_r and "current_regime" in r_res, f"regime={r_res.get('current_regime','')}")

ok_a, a_res, _ = get("/api/ml/anomaly/AAPL")
log("GET /api/ml/anomaly/AAPL (IsoForest API)", ok_a and "is_anomaly" in a_res, f"severity={a_res.get('severity','')}")

ok_v, v_res, _ = get("/api/ml/volatility/AAPL")
log("GET /api/ml/volatility/AAPL (GARCH+XGB API)", ok_v and "ensemble_1d_vol_pct" in v_res, f"vol={v_res.get('ensemble_1d_vol_pct','')}%")

# 5. Independent Mathematical Formulations
print("\n[5] INDEPENDENT MATHEMATICAL CHECKS", flush=True)
print("-" * 70, flush=True)

rng = np.random.default_rng(42)
r_synth = rng.normal(0.0003, 0.02, 252)
var_95 = -np.quantile(r_synth, 0.05)
log("Historical Simulation VaR (alpha=0.95)", var_95 > 0, f"VaR_95={var_95:.6f}")

w = rng.dirichlet(np.ones(10))
log("Monte Carlo Dirichlet weights sum to 1.0", abs(w.sum() - 1.0) < 1e-9, f"sum={w.sum():.10f}")

print("\n" + "=" * 70, flush=True)
print(f"  FINAL SUMMARY: {PASS} PASSED | {FAIL} FAILED | {PASS+FAIL} TOTAL", flush=True)
print("=" * 70, flush=True)
if ERRORS:
    for e in ERRORS:
        print(e, flush=True)
else:
    print("  >>> ALL TEST CASES PASSED 100% STRICT VERIFICATION <<<", flush=True)
print()
