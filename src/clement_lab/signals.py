"""Clement/Oliver-Kell signal engine (mechanical part).

Mechanical checklist per transcript + cross-checked with:
- Oliver Kell cycle: wedge-pop -> EMA crossback/base -> base-n-break
  (TraderLion cycle-of-price-action; KellTrading; deepvue screens).
- Minervini VCP/low-cheat + Kulamagi tight+10/20 catch-up (same concept,
  different words — transcript explicitly notes commonality).
- O'Neil: RS line > own MA, price >50d & >200d sloping up.

Signals (daily bars, no intraday peeking):
1. stage2: Close>50d SMA and Close>200d SMA and both slopes up.
2. wedge_pop: Close crosses above 10d EMA and 20d EMA after being below
   (accumulation character change).
3. launch_pad: consolidation after wedge_pop: range contracts, volume dry-up,
   close above 20d EMA, VCP proxy true at least once in last 10 bars.
4. breakout_trigger: Close breaks highest-high of last N=20 bars with
   volume > 1.2x 20d mean (demand arrives on low supply).
5. pullback_trigger: Close pulls into 10d/20d EMA zone (±1.5%) while stage2
   holds and RS-above-MA holds -> buy weakness with tight stop.
6. extension veto: distance from 50d SMA > 4*ATR => SKIP (meat off bone).
7. breakdown (short watch): Close breaks BELOW 20d EMA after stage2 ->
   demote to short list (transcript: "gets demoted into that list").

All triggers are computed t -> signal for t+1 open (no look-ahead).
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from .indicators import ema, sma, atr, adr_percent, avg_dollar_volume, rs_above_own_ma, volatility_contraction, volume_dryup


def add_features(df: pd.DataFrame, index_close: pd.Series | None = None) -> pd.DataFrame:
    d = df.copy()
    c = d["Close"]
    d["ema10"] = ema(c, 10)
    d["ema20"] = ema(c, 20)
    d["sma50"] = sma(c, 50)
    d["sma200"] = sma(c, 200)
    d["sma50_up"] = d["sma50"] > d["sma50"].shift(5)
    d["sma200_up"] = d["sma200"] > d["sma200"].shift(10)
    d["atr14"] = atr(d, 14)
    d["adr20"] = adr_percent(d, 20)
    d["adv50"] = avg_dollar_volume(d, 50)
    d["vol_mean20"] = d["Volume"].rolling(20, min_periods=20).mean()
    d["vol_dry"] = volume_dryup(d["Volume"], 20, 0.7)
    d["vcp"] = volatility_contraction(c, 10, 3)
    d["hh20"] = c.rolling(20, min_periods=20).max()
    d["dist_50_atr"] = (c - d["sma50"]) / d["atr14"].replace(0, np.nan)
    d["was_below_emas"] = (c.shift(1) < d["ema10"].shift(1)) | (c.shift(1) < d["ema20"].shift(1))
    if index_close is not None:
        rs = rs_above_own_ma(c, index_close, 21)
        d["rs_ok"] = rs.reindex(d.index).fillna(False)
    else:
        d["rs_ok"] = True
    return d


def compute_signals(d: pd.DataFrame, adv_min: float = 50_000_000, adr_min: float = 3.0) -> pd.DataFrame:
    d = d.copy()
    d["liquid"] = d["adv50"] >= adv_min
    d["volatile_enough"] = d["adr20"] >= adr_min
    d["stage2"] = (d["Close"] > d["sma50"]) & (d["Close"] > d["sma200"]) & d["sma50_up"] & d["sma200_up"]
    d["wedge_pop"] = d["was_below_emas"] & (d["Close"] > d["ema10"]) & (d["Close"] > d["ema20"])
    # launch pad: after pop, tight + above 20ema + (dry volume or recent VCP)
    recent_vcp = d["vcp"].rolling(10, min_periods=1).max().fillna(0).astype(bool)
    d["launch_pad"] = (
        (d["Close"] > d["ema20"])
        & (d["vol_dry"] | recent_vcp)
        & d["stage2"]
    )
    d["breakout_trigger"] = (
        (d["Close"] > d["hh20"].shift(1))
        & (d["Volume"] > 1.2 * d["vol_mean20"])
        & d["stage2"] & d["liquid"] & d["volatile_enough"] & d["rs_ok"]
        & (d["dist_50_atr"] < 4.0)
    )
    ema_zone = ((d["Close"] - d["ema20"]).abs() / d["ema20"] < 0.015) | ((d["Close"] - d["ema10"]).abs() / d["ema10"] < 0.015)
    d["pullback_trigger"] = (
        ema_zone & d["stage2"] & d["liquid"] & d["volatile_enough"] & d["rs_ok"]
        & (d["dist_50_atr"] < 4.0) & (d["Close"] > d["ema20"] * 0.98)
    )
    d["extended_veto"] = d["dist_50_atr"] >= 4.0
    d["breakdown"] = (d["Close"] < d["ema20"]) & d["stage2"].shift(1).fillna(False)
    # tradable long = (breakout OR pullback) and not extended
    d["long_signal"] = (d["breakout_trigger"] | d["pullback_trigger"]) & (~d["extended_veto"])
    return d
