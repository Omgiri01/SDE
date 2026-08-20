"""
sentiment_analyzer.py
---------------------
Author: Om Giri (github.com/Omgiri01)
QuantRiskPro ML Module 5/5: Financial News Sentiment Analysis

Model: FinBERT (ProsusAI/finbert) — BERT fine-tuned on financial text
       Falls back to VADER (rule-based) if transformers unavailable

Why FinBERT over generic BERT/VADER:
  - VADER was designed for social media; misclassifies financial jargon
    e.g., "The stock rallied on strong earnings" → VADER: neutral (wrong)
    FinBERT correctly identifies this as positive sentiment
  - FinBERT was trained on 4,500 financial news articles from Reuters,
    Bloomberg, and FT — it understands domain-specific language:
    "margin compression", "downgraded to underperform", "beat estimates"
  - Output is (positive, negative, neutral) probabilities per sentence

Pipeline:
  Raw news headline
    → FinBERT tokenizer (WordPiece, max_length=512)
    → BERT encoder (12 layers, 768 hidden)
    → CLS token → Linear classifier
    → Softmax (positive, negative, neutral)

Usage in QuantRiskPro:
  - Fetch recent headlines for a ticker (Alpha Vantage / NewsAPI)
  - Score each headline → aggregate to bull/bear/neutral signal
  - Feed signal as additional feature to the portfolio optimizer
  - Stream sentiment shifts via WebSocket to dashboard
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SentimentResult:
    text: str
    positive: float
    negative: float
    neutral: float
    label: str           # "positive" | "negative" | "neutral"
    confidence: float
    model: str
    financial_signal: str   # "BULLISH" | "BEARISH" | "NEUTRAL"
    signal_strength: float  # 0 to 1


@dataclass
class AggregatedSentiment:
    ticker: str
    headlines_analyzed: int
    avg_positive: float
    avg_negative: float
    avg_neutral: float
    aggregate_signal: str       # "BULLISH" | "BEARISH" | "NEUTRAL"
    bull_bear_ratio: float      # > 1 = more bullish headlines
    sentiment_score: float      # -1 (very bearish) to +1 (very bullish)
    results: list = field(default_factory=list)


class SentimentAnalyzer:
    """
    Financial news sentiment analyzer using FinBERT.
    Falls back to keyword-based scoring if transformers not available.
    """

    def __init__(self, use_finbert: bool = True):
        self.pipeline = None
        self.model_name = "ProsusAI/finbert"
        self.is_loaded = False
        self._use_finbert = use_finbert

    def load(self) -> dict:
        """Load FinBERT model. Call once at startup (takes ~5s first time)."""
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                top_k=None,  # return all 3 class probabilities
                truncation=True,
                max_length=512,
            )
            self.is_loaded = True
            return {"model": "FinBERT (ProsusAI/finbert)", "status": "loaded", "device": "cpu"}
        except Exception as e:
            self.is_loaded = True
            self._use_finbert = False
            return {"model": "Keyword-based fallback", "status": f"FinBERT unavailable: {e}"}

    def _keyword_score(self, text: str) -> SentimentResult:
        """
        Rule-based financial sentiment using curated keyword lists.
        Used as fallback when FinBERT is not available.
        """
        text_lower = text.lower()

        bullish_keywords = [
            "beat", "beats", "exceeded", "surpassed", "rally", "rallied", "surge",
            "soared", "upgraded", "upgrade", "buy rating", "outperform", "strong",
            "record", "profit", "growth", "positive", "bullish", "recovery",
            "raised guidance", "dividend increase", "buyback", "acquisition deal",
        ]
        bearish_keywords = [
            "miss", "missed", "below", "downgrade", "downgraded", "cut", "slashed",
            "sell rating", "underperform", "decline", "dropped", "crashed", "weak",
            "loss", "layoff", "layoffs", "bankruptcy", "debt", "warning",
            "lowered guidance", "recall", "lawsuit", "investigation", "fraud",
        ]

        bull_count = sum(1 for kw in bullish_keywords if kw in text_lower)
        bear_count = sum(1 for kw in bearish_keywords if kw in text_lower)
        total = bull_count + bear_count

        if total == 0:
            pos, neg, neu = 0.1, 0.1, 0.8
            label = "neutral"
        elif bull_count > bear_count:
            pos = 0.4 + 0.1 * min(bull_count, 5)
            neg = 0.1
            neu = max(0.0, 1.0 - pos - neg)
            label = "positive"
        elif bear_count > bull_count:
            neg = 0.4 + 0.1 * min(bear_count, 5)
            pos = 0.1
            neu = max(0.0, 1.0 - pos - neg)
            label = "negative"
        else:
            pos, neg, neu = 0.3, 0.3, 0.4
            label = "neutral"

        confidence = max(pos, neg, neu)

        signal = "BULLISH" if label == "positive" else ("BEARISH" if label == "negative" else "NEUTRAL")
        strength = abs(pos - neg)

        return SentimentResult(
            text=text[:200],
            positive=round(pos, 4),
            negative=round(neg, 4),
            neutral=round(neu, 4),
            label=label,
            confidence=round(confidence, 4),
            model="Keyword-based (FinBERT fallback)",
            financial_signal=signal,
            signal_strength=round(strength, 4),
        )

    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single financial news headline or sentence."""
        if not self.is_loaded:
            self.load()

        text = re.sub(r'\s+', ' ', text.strip())[:512]

        if self._use_finbert and self.pipeline is not None:
            try:
                raw = self.pipeline(text)[0]
                scores = {item["label"].lower(): item["score"] for item in raw}
                pos = scores.get("positive", 0.0)
                neg = scores.get("negative", 0.0)
                neu = scores.get("neutral", 0.0)
                label = max(scores, key=scores.get)
                confidence = max(pos, neg, neu)
                signal = "BULLISH" if label == "positive" else ("BEARISH" if label == "negative" else "NEUTRAL")
                strength = abs(pos - neg)
                return SentimentResult(
                    text=text[:200],
                    positive=round(pos, 4),
                    negative=round(neg, 4),
                    neutral=round(neu, 4),
                    label=label,
                    confidence=round(confidence, 4),
                    model="FinBERT (ProsusAI/finbert)",
                    financial_signal=signal,
                    signal_strength=round(strength, 4),
                )
            except Exception:
                pass

        return self._keyword_score(text)

    def analyze_batch(self, ticker: str, headlines: list) -> AggregatedSentiment:
        """
        Analyze a batch of headlines for a ticker and aggregate signals.
        Returns composite bull/bear signal for portfolio decision making.
        """
        if not headlines:
            return AggregatedSentiment(
                ticker=ticker, headlines_analyzed=0,
                avg_positive=0.33, avg_negative=0.33, avg_neutral=0.34,
                aggregate_signal="NEUTRAL", bull_bear_ratio=1.0,
                sentiment_score=0.0,
            )

        results = [self.analyze(h) for h in headlines]

        avg_pos = sum(r.positive for r in results) / len(results)
        avg_neg = sum(r.negative for r in results) / len(results)
        avg_neu = sum(r.neutral for r in results) / len(results)

        bull_count = sum(1 for r in results if r.financial_signal == "BULLISH")
        bear_count = sum(1 for r in results if r.financial_signal == "BEARISH")
        bull_bear_ratio = bull_count / max(bear_count, 1)

        # Sentiment score: -1 (very bearish) to +1 (very bullish)
        sentiment_score = avg_pos - avg_neg

        if sentiment_score > 0.15:
            aggregate = "BULLISH 📈"
        elif sentiment_score < -0.15:
            aggregate = "BEARISH 📉"
        else:
            aggregate = "NEUTRAL ➡️"

        return AggregatedSentiment(
            ticker=ticker,
            headlines_analyzed=len(headlines),
            avg_positive=round(avg_pos, 4),
            avg_negative=round(avg_neg, 4),
            avg_neutral=round(avg_neu, 4),
            aggregate_signal=aggregate,
            bull_bear_ratio=round(bull_bear_ratio, 2),
            sentiment_score=round(sentiment_score, 4),
            results=[{
                "text": r.text[:100],
                "signal": r.financial_signal,
                "confidence": r.confidence,
            } for r in results],
        )


# Sample financial headlines for demo mode
DEMO_HEADLINES = {
    "AAPL": [
        "Apple beats Q3 earnings estimates, revenue surges 8% YoY",
        "iPhone sales in China declined as competition intensifies",
        "Apple announces $110B share buyback program, largest in history",
    ],
    "TSLA": [
        "Tesla misses delivery estimates for third consecutive quarter",
        "Tesla Cybertruck production ramp exceeds expectations",
        "Elon Musk sells additional $3.5B in Tesla shares amid margin pressure",
    ],
    "NVDA": [
        "Nvidia data center revenue triples, crushes Wall Street estimates",
        "Nvidia announces Blackwell GPU architecture with 2x performance gains",
        "Nvidia stock upgraded to strong buy by 12 analysts following AI boom",
    ],
    "MSFT": [
        "Microsoft Azure revenue growth accelerates to 31%, beats estimates",
        "Microsoft Copilot AI integration drives enterprise subscription growth",
        "Microsoft acquires gaming studio in $68.7B deal, regulators approve",
    ],
}
