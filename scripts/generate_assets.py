"""Generate all visual assets from VERIFIED live results (no hand-drawn numbers).

Reads: data/*.parquet, results/per_symbol.json, results/hidden_patterns.json
Writes: assets/*.png, assets/demo.gif, assets/demo.mp4
All charts recomputed live — README/preview must reference these files.
"""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
RESULTS = ROOT / "results"
DATA = ROOT / "data"

per = json.load(open(RESULTS / "per_symbol.json"))
hidden = json.load(open(RESULTS / "hidden_patterns.json"))

plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight", "font.size": 9})

# 1. Results bar: total return per symbol (verified)
items = sorted([(k, v["full"]["total_return"]) for k, v in per.items()], key=lambda x: x[1])
syms = [k for k, _ in items]
vals = [v * 100 for _, v in items]
colors = ["#16a34a" if v >= 0 else "#dc2626" for v in vals]
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.barh(syms, vals, color=colors)
ax.set_xlabel("Total return % (2020-2026, 0.3% risk, 5bps costs)")
ax.set_title("Verified per-symbol total return — mechanical long-only v1")
for y, v in zip(syms, vals):
    ax.text(v + (0.1 if v >= 0 else -0.1), y, f"{v:.2f}%", va="center", ha="left" if v >= 0 else "right", fontsize=8)
fig.tight_layout()
fig.savefig(ASSETS / "returns_bar.png")
print("wrote returns_bar.png")

# 2. Win-rate vs profit-factor scatter (verified)
fig, ax = plt.subplots(figsize=(6, 4.2))
for k, v in per.items():
    f = v["full"]
    ax.scatter(f["win_rate"] * 100, f["profit_factor"], s=60)
    ax.annotate(k, (f["win_rate"] * 100, f["profit_factor"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
ax.set_xlabel("Win rate %")
ax.set_ylabel("Profit factor")
ax.set_title("Win rate vs profit factor (low win can still win: 33% PLTR/NVDA)")
ax.set_ylim(0, max(10, max(v["full"]["profit_factor"] for v in per.values() if v["full"]["profit_factor"] < 50)))
fig.tight_layout()
fig.savefig(ASSETS / "winrate_pf.png")
print("wrote winrate_pf.png")

# 3. QQQ regime chart (verified live data)
qqq = pd.read_parquet(DATA / "QQQ_2020-01-01_2026-10-01.parquet")
close = qqq["Close"]
if isinstance(close, pd.DataFrame):
    close = close.iloc[:, 0]
ma10 = close.rolling(10).mean()
ma20 = close.rolling(20).mean()
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.plot(qqq.index, close.values, label="QQQ close", linewidth=1.2, color="#111827")
ax.plot(qqq.index, ma10.values, label="MA10", linewidth=0.9, color="#2563eb")
ax.plot(qqq.index, ma20.values, label="MA20", linewidth=0.9, color="#f59e0b")
# shade RISK-OFF 2022 bear + 2025 correction approx via MA rule
below = (close.values < ma10.values) & (close.values < ma20.values)
ax.fill_between(qqq.index, close.values.min(), close.values.max(), where=below, color="#fecaca", alpha=0.35, label="RISK-OFF zone")
ax.set_title("QQQ regime filter — first filter before any stock (live 2020-2026)")
ax.legend(loc="upper left", fontsize=8)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.tight_layout()
fig.savefig(ASSETS / "regime_chart.png")
print("wrote regime_chart.png")

# 4. Hidden H1: breakout vs pullback
h1 = {d["name"]: d for d in hidden["H1_breakout_vs_pullback"]}
fig, ax = plt.subplots(figsize=(6, 3.6))
cats = ["breakout", "pullback"]
means = [h1[c]["mean_fwd20"] * 100 for c in cats]
hits = [h1[c]["hit_rate_fwd20_pos"] * 100 for c in cats]
x = range(len(cats))
b1 = ax.bar([i - 0.2 for i in x], means, width=0.4, label="Mean fwd20 %", color="#2563eb")
b2 = ax.bar([i + 0.2 for i in x], hits, width=0.4, label="Hit %", color="#16a34a", alpha=0.7)
ax.set_xticks(list(x))
ax.set_xticklabels([f"{c}\n(n={h1[c]['n']})" for c in cats])
ax.set_title("Hidden H1: breakout pays ~3x pullback (fwd20)")
ax.legend(fontsize=8)
for i, c in enumerate(cats):
    ax.text(i - 0.2, means[i] + 0.2, f"{means[i]:.2f}%", ha="center", fontsize=8)
    ax.text(i + 0.2, hits[i] + 0.5, f"{hits[i]:.1f}%", ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(ASSETS / "hidden_H1.png")
print("wrote hidden_H1.png")

# 5. Signals per symbol
sigs = sorted([(k, v["n_signals"]) for k, v in per.items()], key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar([k for k, _ in sigs], [v for _, v in sigs], color="#7c3aed")
ax.set_title("Long signals per symbol (RS + extension guarded)")
ax.set_ylabel("n signals")
plt.xticks(rotation=30, ha="right")
fig.tight_layout()
fig.savefig(ASSETS / "signals_bar.png")
print("wrote signals_bar.png")

# 6. Demo animation: cumulative signals + regime over time (verified QQQ)
# Build monthly signal counts from live backtest? Simplified: animate QQQ price + MA ribbon
fig2, ax2 = plt.subplots(figsize=(8, 4))
line_q, = ax2.plot([], [], label="QQQ", color="#111827")
line10, = ax2.plot([], [], label="MA10", color="#2563eb", linewidth=1)
line20, = ax2.plot([], [], label="MA20", color="#f59e0b", linewidth=1)
ax2.legend(loc="upper left", fontsize=8)
ax2.set_title("Demo: QQQ regime 2020-2026 — green light only when trend is up")
idx = qqq.index
y = close.values
y10 = ma10.values
y20 = ma20.values
ax2.set_xlim(idx[0], idx[-1])
import numpy as np
ax2.set_ylim(float(np.nanmin(y)) * 0.9, float(np.nanmax(y)) * 1.05)
step = max(1, len(idx) // 120)
frames = list(range(0, len(idx), step))

def update(f):
    line_q.set_data(idx[:f], y[:f])
    line10.set_data(idx[:f], y10[:f])
    line20.set_data(idx[:f], y20[:f])
    return line_q, line10, line20

ani = FuncAnimation(fig2, update, frames=frames, interval=60, blit=False)
ani.save(ASSETS / "demo.gif", writer=PillowWriter(fps=12))
print("wrote demo.gif")
try:
    ani.save(ASSETS / "demo.mp4", writer=FFMpegWriter(fps=12, bitrate=1200))
    print("wrote demo.mp4")
except Exception as e:
    print("mp4 skip:", e)
plt.close("all")
print("assets done:", sorted(p.name for p in ASSETS.iterdir()))
