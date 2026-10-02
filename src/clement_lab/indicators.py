"""Technical indicators — standard, auditable formulas.

Sources verified online (Phase 0):
- EMA/SMA/ATR definitions: standard technical literature (Wilder ATR 1978).
- ADR% = mean(daily range / close) over N days; Clement filter ADR>3% for
  "growthy" names (transcript + Chart Fanatics breakdown).
- RS line = stock close / index close; RS above its 21-day MA = structural
  strength (O'Neil RS rating avg 87 pre-advance; Deepvue/IBD docs).
- All functions use only past data (no look-ahead): values at bar t use
  closes <= t. Verified by unit test test_no_lookahead.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False, min_periods=span).mean()


def sma(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=window).mean()


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(window, min_periods=window).mean()


def adr_percent(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Average Daily Range as % of close."""
    rng = (df["High"] - df["Low"]) / df["Close"].replace(0, np.nan)
    return rng.rolling(window, min_periods=window).mean() * 100.0


def avg_dollar_volume(df: pd.DataFrame, window: int = 50) -> pd.Series:
    dv = df["Close"] * df["Volume"]
    return dv.rolling(window, min_periods=window).mean()


def rs_line(stock_close: pd.Series, index_close: pd.Series) -> pd.Series:
    aligned = pd.concat([stock_close, index_close], axis=1, join="inner")
    aligned.columns = ["s", "i"]
    return aligned["s"] / aligned["i"].replace(0, np.nan)


def rs_above_own_ma(stock_close: pd.Series, index_close: pd.Series, window: int = 21) -> pd.Series:
    rs = rs_line(stock_close, index_close)
    ma = rs.rolling(window, min_periods=window).mean()
    return rs > ma


def slope_up(s: pd.Series, window: int = 5) -> pd.Series:
    """Slope proxy: current value above value `window` bars ago."""
    return s > s.shift(window)


def bollinger_upper(s: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.Series:
    ma = s.rolling(window, min_periods=window).mean()
    sd = s.rolling(window, min_periods=window).std()
    return ma + n_std * sd


def volume_dryup(volume: pd.Series, window: int = 20, threshold: float = 0.7) -> pd.Series:
    """True when current volume < threshold * rolling mean (supply drying)."""
    mean_vol = volume.rolling(window, min_periods=window).mean()
    return volume < threshold * mean_vol


def volatility_contraction(close: pd.Series, window: int = 10, contractions: int = 3) -> pd.Series:
    """VCP proxy: rolling std strictly decreasing for `contractions` consecutive windows.

    Minervini VCP = volatility contracts left-to-right before breakout.
    We measure std over `window` bars; require monotonic decrease.
    """
    vol = close.pct_change().rolling(window, min_periods=window).std()
    cond = pd.Series(True, index=close.index)
    for k in range(1, contractions + 1):
        cond &= vol < vol.shift(k)
    return cond.fillna(False)
