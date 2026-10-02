"""Fetch live public data (Yahoo) into data/ cache. Verifies real-data path."""
import argparse, yaml
from pathlib import Path
from clement_lab.data_loader import download

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    syms = [cfg["universe"]["index"], cfg["universe"]["market"]] + cfg["universe"]["leaders_2023_2025"]
    syms = list(dict.fromkeys(syms))
    out = download(syms, cfg["period"]["start"], cfg["period"]["end"], use_cache=False)
    for k, df in out.items():
        if len(df) == 0:
            print(f"{k}: EMPTY — skipped")
            continue
        close_last = float(df["Close"].iloc[-1]) if hasattr(df["Close"].iloc[-1], "__float__") else float(df["Close"].iloc[-1].iloc[0])
        print(f"{k}: {df.index[0].date()} -> {df.index[-1].date()} rows={len(df)} last_close={close_last:.2f}")
