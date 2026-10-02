"""Market-regime filter (first filter before any stock setup).

Rule distilled from transcript + verification sources:
- QQQ (or SPY) trending ABOVE 10-day and 20-day MA with both sloping up
  => RISK-ON (trending). Expect breakouts to follow through.
- QQQ BELOW all relevant MAs => RISK-OFF (correction/bear).
  "Any breakout you find will fail" (transcript).
- Else CHOPPY.

Exposure map (Clement progressive exposure + Minervini exposure logic):
- RISK-ON  -> exposure 1.0 (full normal risk)
- CHOPPY   -> exposure 0.25 (starter / chip-away)
- RISK-OFF -> exposure 0.0 long (cash; shorts allowed in separate engine)

Verified against 2020-2026 QQQ history in exp01.
"""
from __future__ import annotations
import pandas as pd
from .indicators import sma, slope_up


def compute_regime(index_df: pd.DataFrame) -> pd.DataFrame:
    close = index_df["Close"]
    ma10 = sma(close, 10)
    ma20 = sma(close, 20)
    out = pd.DataFrame(index=index_df.index)
    out["close"] = close
    out["ma10"] = ma10
    out["ma20"] = ma20
    out["ma10_up"] = slope_up(ma10, 5)
    out["ma20_up"] = slope_up(ma20, 5)
    out["above10"] = close > ma10
    out["above20"] = close > ma20
    out["below10"] = close < ma10
    out["below20"] = close < ma20

    def label(r):
        if pd.isna(r["ma10"]) or pd.isna(r["ma20"]):
            return "WARMUP"
        if r["above10"] and r["above20"] and r["ma10_up"] and r["ma20_up"]:
            return "RISK-ON"
        if r["below10"] and r["below20"]:
            return "RISK-OFF"
        return "CHOPPY"

    out["regime"] = out.apply(label, axis=1)
    out["exposure"] = out["regime"].map({"RISK-ON": 1.0, "CHOPPY": 0.25, "RISK-OFF": 0.0, "WARMUP": 0.0})
    return out
