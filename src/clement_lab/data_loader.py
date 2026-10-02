"""Yahoo Finance live-data loader (public data verification).

- Uses yfinance (public Yahoo API, research/educational use).
- Daily bars, auto_adjust=False to keep Volume true; we use Adj Close logic
  via `auto_adjust=True` variant? We keep Close adjusted by yfinance when
  auto_adjust=True. Chosen: auto_adjust=True for survivorship of splits/divs.
- Caches to data/*.parquet for reproducibility + offline rerun.
- No look-ahead: download once, all indicators shift-aware.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def download(symbols: list[str], start: str, end: str, use_cache: bool = True) -> dict[str, pd.DataFrame]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        fp = DATA_DIR / f"{sym}_{start}_{end}.parquet"
        if use_cache and fp.exists():
            df_cached = pd.read_parquet(fp)
            if len(df_cached) > 0:
                out[sym] = df_cached
                continue
        df = yf.download(sym, start=start, end=end, auto_adjust=True, progress=False, actions=False)
        if df is None or len(df) == 0:
            print(f"WARN skip {sym}: empty download (delisted/bad symbol)")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            # yfinance multi-ticker frame -> flatten
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns={c: c.capitalize() if isinstance(c, str) else c for c in df.columns})
        # ensure required cols
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                print(f"WARN skip {sym}: missing {col}")
                df = pd.DataFrame()
                break
        if len(df) == 0:
            continue
        df = df.dropna(subset=["Close"])
        if len(df) == 0:
            print(f"WARN skip {sym}: all-NaN after dropna")
            continue
        df.to_parquet(fp)
        out[sym] = df
    if not out:
        raise RuntimeError("No symbols downloaded — check network/tickers")
    return out
