"""Hidden-pattern discovery on LIVE data (voting across filters).

H1: Breakout vs pullback — which leg pays?
H2: Launch-pad (dry volume + VCP) conditioning — does it lift win rate?
H3: Regime-conditioned hit rate — RISK-ON vs CHOPPY vs RISK-OFF.
H4: Extension veto — entries >4 ATR from 50d: lottery or trap?
H5: Concentration — do top-3 names drive portfolio (7-winner rule)?
H6: Sizing sweep — fixed 1% vs dynamic 0.3/0.5/1% (maxDD vs return).
H7: Walk-forward — 2020-22 train vs 2023-26 test stability.

All outputs -> results/hidden_patterns.json (README cites verbatim).
"""
import json, yaml
from pathlib import Path
import pandas as pd
from clement_lab.data_loader import download
from clement_lab.regime import compute_regime
from clement_lab.signals import add_features, compute_signals
from clement_lab.backtest import backtest_single, metrics_from_equity
from clement_lab.sizing import SizingConfig
from clement_lab.backtest import CostConfig

cfg = yaml.safe_load(open("configs/default.yaml"))
symbols = cfg["universe"]["leaders_2023_2025"]
START, END = cfg["period"]["start"], cfg["period"]["end"]
data = download(symbols + [cfg["universe"]["index"]], START, END, use_cache=True)
idx = data[cfg["universe"]["index"]]
regime = compute_regime(idx)

# per-bar analysis frame
rows = []
for s in symbols:
    if s not in data:
        continue
    feat = add_features(data[s], idx["Close"])
    sig = compute_signals(feat, cfg["filters"]["adv_min"], cfg["filters"]["adr_min"])
    sig["symbol"] = s
    # forward 20d return (information only, not traded; measures setup quality)
    fwd = data[s]["Close"].shift(-20) / data[s]["Close"] - 1
    # align
    tmp = pd.DataFrame({"breakout": sig["breakout_trigger"], "pullback": sig["pullback_trigger"],
                        "launch": sig["launch_pad"], "rs": sig["rs_ok"], "ext": sig["extended_veto"],
                        "fwd20": fwd})
    tmp["regime"] = regime["regime"].reindex(tmp.index, method="ffill")
    tmp["symbol"] = s
    rows.append(tmp)
allb = pd.concat(rows)

def grp_stats(mask, name):
    sub = allb[mask]
    return {"name": name, "n": int(sub["fwd20"].notna().sum()),
            "mean_fwd20": float(sub["fwd20"].mean()),
            "median_fwd20": float(sub["fwd20"].median()),
            "hit_rate_fwd20_pos": float((sub["fwd20"] > 0).mean()) if len(sub) else 0.0}

out = {}
out["H1_breakout_vs_pullback"] = [grp_stats(allb["breakout"], "breakout"), grp_stats(allb["pullback"], "pullback")]
out["H2_launchpad"] = [grp_stats(allb["launch"], "launch_pad_true"), grp_stats(~allb["launch"], "launch_pad_false")]
out["H3_regime_fwd"] = [grp_stats(allb["regime"] == r, r) for r in ["RISK-ON", "CHOPPY", "RISK-OFF"]]
# extension: compare vetoed (extended) hypothetical entries vs allowed
out["H4_extension"] = [grp_stats(allb["ext"], "extended_vetoed"), grp_stats(~allb["ext"], "not_extended")]
# H5 concentration: run backtests, rank by total_return
sizing = SizingConfig()
costs = CostConfig()
totals = {}
for s in symbols:
    if s not in data:
        continue
    feat = add_features(data[s], idx["Close"])
    sig = compute_signals(feat, cfg["filters"]["adv_min"], cfg["filters"]["adr_min"])
    sig["symbol"] = s
    eq, tr = backtest_single(sig, regime, sizing=sizing, costs=costs)
    m = metrics_from_equity(eq, tr)
    totals[s] = m.get("total_return", 0)
ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
out["H5_concentration_rank"] = [{"symbol": k, "total_return": float(v)} for k, v in ranked]
top3 = sum(v for _, v in ranked[:3]); all_sum = sum(totals.values())
out["H5_top3_share"] = float(top3 / all_sum) if all_sum != 0 else 0.0
# H6 sizing sweep on NVDA representative + portfolio proxy (equal-weight of per-symbol equity not implemented; use NVDA)
feat = add_features(data["NVDA"], idx["Close"])
signv = compute_signals(feat, cfg["filters"]["adv_min"], cfg["filters"]["adr_min"])
signv["symbol"] = "NVDA"
sweep = {}
for name, sz in [("fixed_1pct", SizingConfig(0.01, 0.01, 0.01, 0.01, 0.01)),
                 ("dynamic_clement", SizingConfig()),
                 ("tiny_0.1pct", SizingConfig(0.001, 0.001, 0.001, 0.001, 0.001))]:
    eq, tr = backtest_single(signv, regime, sizing=sz, costs=costs)
    sweep[name] = metrics_from_equity(eq, tr)
out["H6_sizing_NVDA"] = sweep
# H7 walk-forward: train 2020-22 vs test 2023-26 (same rules, no re-opt = stability check)
def run_window(a, b):
    dd = {k: v.loc[a:b] for k, v in data.items() if k in data}
    if len(dd[cfg["universe"]["index"]]) < 50:
        return {}
    rg = compute_regime(dd[cfg["universe"]["index"]])
    res = {}
    for s in symbols:
        if s not in dd or len(dd[s]) < 60:
            continue
        f = add_features(dd[s], dd[cfg["universe"]["index"]]["Close"])
        sg = compute_signals(f, cfg["filters"]["adv_min"], cfg["filters"]["adr_min"])
        sg["symbol"] = s
        eq, tr = backtest_single(sg, rg, sizing=sizing, costs=costs)
        res[s] = metrics_from_equity(eq, tr)
    return res
out["H7_train_2020_2022"] = run_window("2020-01-01", "2022-12-31")
out["H7_test_2023_2026"] = run_window("2023-01-01", "2026-10-01")

Path("results").mkdir(exist_ok=True)
json.dump(out, open("results/hidden_patterns.json", "w"), indent=2, default=str)
print(json.dumps({k: (v if not isinstance(v, dict) else list(v.keys())) for k, v in out.items()}, indent=2))
for h in ["H1_breakout_vs_pullback", "H2_launchpad", "H3_regime_fwd", "H4_extension"]:
    print(h, out[h])
print("H5 rank", out["H5_concentration_rank"][:5], "top3_share", out["H5_top3_share"])
print("H6", {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in out["H6_sizing_NVDA"].items()})
