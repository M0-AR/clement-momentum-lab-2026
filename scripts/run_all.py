"""Run all verification experiments end-to-end on LIVE public data.

Produces results/*.json + results/summary.md consumed by README (PhD paper).
Every number in README must come from these outputs — no hand-written stats.
"""
import argparse, json, yaml
from pathlib import Path
import pandas as pd
from clement_lab.data_loader import download
from clement_lab.regime import compute_regime
from clement_lab.signals import add_features, compute_signals
from clement_lab.backtest import backtest_single, metrics_from_equity
from clement_lab.sizing import SizingConfig
from clement_lab.backtest import CostConfig

def load_cfg(p):
    import yaml
    return yaml.safe_load(open(p))

def run_period(symbols, index_sym, start, end, adv_min, adr_min, sizing, costs):
    data = download(symbols + [index_sym], start, end, use_cache=True)
    idx = data[index_sym]
    regime = compute_regime(idx)
    # buy-hold benchmark
    bh = idx["Close"] / idx["Close"].iloc[0]
    per_symbol = {}
    for s in symbols:
        df = data[s]
        feat = add_features(df, idx["Close"])
        sig = compute_signals(feat, adv_min, adr_min)
        sig["symbol"] = s
        eq, tr = backtest_single(sig, regime, sizing=sizing, costs=costs)
        m = metrics_from_equity(eq, tr)
        # ablation: no regime (always exposure 1.0)
        regime_off = regime.copy(); regime_off["exposure"] = 1.0; regime_off["regime"] = "RISK-ON"
        eq_nr, tr_nr = backtest_single(sig, regime_off, sizing=sizing, costs=costs)
        m_nr = metrics_from_equity(eq_nr, tr_nr)
        # ablation: no RS — recompute features WITHOUT index (rs_ok=True path)
        feat_nors = add_features(df, None)
        sig_nors = compute_signals(feat_nors, adv_min, adr_min)
        sig_nors["symbol"] = s
        eq_nors, tr_nors = backtest_single(sig_nors, regime, sizing=sizing, costs=costs)
        m_nors = metrics_from_equity(eq_nors, tr_nors)
        # ablation: no extension veto (allow extended entries)
        sig_noext = sig.copy()
        sig_noext["long_signal"] = sig_noext["breakout_trigger"] | sig_noext["pullback_trigger"]
        eq_noext, tr_noext = backtest_single(sig_noext, regime, sizing=sizing, costs=costs)
        m_noext = metrics_from_equity(eq_noext, tr_noext)
        per_symbol[s] = {"full": m, "no_regime": m_nr, "no_rs": m_nors, "no_extension_veto": m_noext,
                         "n_signals": int(sig["long_signal"].sum()),
                         "n_signals_no_rs": int(sig_nors["long_signal"].sum()),
                         "n_signals_no_ext": int(sig_noext["long_signal"].sum()),
                         "last_close": float(df["Close"].iloc[-1]) if len(df) else 0.0}
    return per_symbol, regime

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--period", default=None)
    ap.add_argument("--run-all", action="store_true")
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    if args.period and ":" in args.period:
        s, e = args.period.split(":")
        cfg["period"]["start"], cfg["period"]["end"] = s, e
    symbols = cfg["universe"]["leaders_2023_2025"]
    sizing = SizingConfig(normal_risk=cfg["risk"]["normal_risk"], strong_risk=cfg["risk"]["strong_risk"],
                          conviction_risk=cfg["risk"]["conviction_risk"], starter_risk=cfg["risk"]["starter_risk"],
                          minuscule_risk=cfg["risk"]["minuscule_risk"], monthly_floor=cfg["risk"]["monthly_floor"])
    costs = CostConfig(bps_per_side=cfg["costs"]["bps_per_side"])
    out, regime = run_period(symbols, cfg["universe"]["index"], cfg["period"]["start"], cfg["period"]["end"],
                             cfg["filters"]["adv_min"], cfg["filters"]["adr_min"], sizing, costs)
    Path("results").mkdir(exist_ok=True)
    json.dump(out, open("results/per_symbol.json", "w"), indent=2)
    # regime distribution (hidden-pattern input)
    dist = regime["regime"].value_counts(normalize=True).to_dict()
    json.dump({str(k): float(v) for k, v in dist.items()}, open("results/regime_mix.json", "w"), indent=2)
    # summary markdown (machine-generated, README must cite it)
    lines = ["# Auto-generated verification summary (DO NOT hand-edit)", ""]
    for s, m in out.items():
        f = m["full"]
        lines.append(f"- {s}: n_trades={f.get('n_trades',0)} win={f.get('win_rate',0):.2%} pf={f.get('profit_factor',0):.2f} sharpe={f.get('sharpe',0):.2f} mdd={f.get('max_drawdown',0):.2%} total={f.get('total_return',0):.2%} | no_regime_total={m['no_regime'].get('total_return',0):.2%} no_rs_total={m['no_rs'].get('total_return',0):.2%} no_ext_total={m['no_extension_veto'].get('total_return',0):.2%} signals={m['n_signals']}/nors={m['n_signals_no_rs']}/noext={m['n_signals_no_ext']}")
    lines += ["", f"Regime mix: {dist}"]
    open("results/summary.md", "w").write("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
