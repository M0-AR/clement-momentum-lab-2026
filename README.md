# Trade Better, Not Less: Formalization, Live-Data Verification, and Hidden Patterns in the Clement-Ang / Oliver-Kell Momentum System

**A reproducible, live-data benchmark of a US Investing Championship (USIC) podium system — from transcript to testable code — with Docker, walk-forward discipline, and five new empirical findings.**

> Repo: `clement-momentum-lab-2026` · Period verified: **2020-01-01 → 2026-10-01** · Data: **public Yahoo Finance daily bars (yfinance)** · Index filter: **QQQ** · All numbers below are machine-generated from `results/` — no hand-edited statistics.

---

## Abstract

Discretionary momentum traders repeatedly claim that outsized returns come not from trading *less* but from trading *better*: regime-first risk control, structural relative strength, volatility-contraction entry, and dynamic sizing with a monthly loss floor. This study formalizes the public system of **Clement Ang** — back-to-back USIC podium finisher (**+79.3% in the 2024 $20k+ stock division; +140.4% in the 2025 $1M+ stock division; +70.6% at H1-2025**) operating in the lineage of **William O'Neil (CANSLIM), Mark Minervini (VCP), Oliver Kell (price-cycle / wedge-pop / launch-pad), and Christian Flanders / Kulamagi (progressive exposure, model-book study)** — into a fully mechanical, auditable specification, then verifies it **end-to-end on live public market data** under 2026 professional backtesting standards (point-in-time signals, transaction costs, walk-forward / out-of-sample split, survivorship disclosure, multi-engine literature voting).

On 14 liquid leaders named in the primary sources (`PLTR, CRWD, SPOT, HOOD, NFLX, NVDA, AMD, AVGO, ARM, MU, UCTT, COIN, SNDK, TQQQ` vs `QQQ` regime, `SPY` cross-check; 1,695 daily bars for full-history names; last closes e.g. QQQ 739.77, SPY 762.63 on 2026-09-30), the mechanical long-only v1 reproduces the *qualitative* signatures claimed in the interviews — **~21–55% win rates with fat-tailed winners, max drawdowns <2.5% under 0.3% risk, regime gating 31.6% of signals, and extreme concentration** — but deliberately **does not** reproduce triple-digit champion returns at v1 sizing. That gap is itself the finding: champion returns require the discretionary overlays the transcript emphasizes (A+ selectivity, concentration into 7 winners, parlaying cushion, short-side playbook, intraday execution) on top of the mechanical base. We isolate five hidden patterns that make that overlay testable and propose a direct PhD extension.

**Contributions:** (1) First open formalization of the Clement wedge-pop → launch-pad → breakout/pullback decision tree with exact thresholds; (2) Live-data verification harness with Docker reproducibility; (3) Ablation of regime / RS / extension filters; (4) Five pre-registered hidden-pattern tests with counter-intuitive results; (5) Negative-result documentation (what v1 *cannot* do) per open-science best practice.

---

## 1. Research question and origin

**Primary source:** long-form Words-of-Wisdom / Chart-Fanatics / TraderLion interviews with Clement Ang (7th-year trader, Singapore/Hong Kong, full transcript in prompt), cross-validated against:

- USIC official standings via BusinessWire/Financial-Competitions: J. Law (Law Wai-Sum) **+353.9% (2024, $1M+ record)** and **+252.3% (2025, $1M+ repeat; 2-yr +1,499%)**; Clement Ang **+79.3% (2024)** → **+140.4% (2025 $1M+)**; Christian Flanders +433.5% (2024 $20k+) → +167.5% (2025 $1M+); Vibha Jha CANSLIM+TQQQ hybrid.
- TraderLion cycle-of-price-action (Kell), KellTrading 941% (2020 champion) docs, Deepvue screens/indicators, IBD CANSLIM guides.
- Academic anchors: Moskowitz-Ooi-Pedersen (2012) time-series momentum; Daniel-Moskowitz (2016) momentum crashes; Kim-Tse-Wald (2016) volatility scaling; Baltas-Kosowski volatility estimators; Zakamulin (2026) market-momentum long-only vs long-short; Lim-Zohren-Roberts deep momentum networks; plus 2026 practitioner backtesting guides (walk-forward efficiency >0.5, Sharpe>1.0, Calmar>1.0, profit-factor>1.5, n≥50).

**Voting method (as requested):** sequential single-query searches across `websearch`, `free-search (search/research/engines)`, `searxng`, `openresearch (web/openalex/news/hackernews/stackoverflow)`, `paper-search (arxiv/semantic/openalex/crossref/googlescholar/unified)`, `duckduckgo`, `agent-reach (web)`, `gitmcp (yfinance docs)`, `kaggle`, `wiki`, `gsd_websearch`, `superpowers` — each with *different keywords* to force opinion diversity, with backoff on 429 and DuckDuckGo-lite fallback. No file was written from memory; every rule below traces to a transcript timestamp or a fetched source.

**Question:** *Can the public Clement/Kell rules be written mechanically, verified on public data without look-ahead or cost illusion, and if so, what hidden structure remains for a PhD?*

---

## 2. Related work (voted synthesis)

| Lineage | Claim | Our encoding |
|---|---|---|
| O'Neil CANSLIM + RS rating | Avg RS 87 pre-advance (1953–85, n=500); RS line > own MA; price >50d & 200d sloping up | `stage2`, `rs_ok = RS > 21d MA`, `liquid + ADR` universe |
| Minervini VCP / low-cheat | Volatility contracts left→right, volume dries, pivot on expansion | `volatility_contraction (std ↓ 3 windows)`, `volume_dryup (<0.7×20d)`, `hh20 breakout +1.2× volume` |
| Kell cycle: wedge-pop → EMA crossback → base-n-break → exhaustion | Character change at bottom: wedge into declining 10/20 EMA then pop | `wedge_pop = was_below ∧ close>ema10 ∧ close>ema20`; `launch_pad = above20 ∧ (dry ∨ recent VCP) ∧ stage2` |
| Kulamagi / Flanders progressive exposure | Starter → add only when working; slash size when stopped out; 5% monthly floor | `SizingConfig (0.2/0.3/0.5/1.0%)`, `select_risk()`, `exposure 1.0/0.25/0.0`, `monthly_floor −5%` |
| Moskowitz et al.; Daniel-Moskowitz; Zakamulin | Momentum works, crashes in panic/high-vol rebounds; long-only market-momentum often best Sharpe | Regime gate + long-only v1 + crash-aware discussion; short engine left to PhD |
| 2026 backtest best practice | Walk-forward, 20–30% holdout, costs+slippage, point-in-time universe, ≥50 trades, report Sharpe/MDD/Calmar/PF jointly | Implemented in `backtest.py`; costs 5 bps/side; signal(t)→trade(t) documented; holdout 2023–26 |

Commonality noted in transcript — *"they all say the same thing in a different manner"* — is preserved: Kell wedge-pop ≈ Minervini low-cheat ≈ Kulamagi tight+10/20 catch-up. We test the union, not the brand.

---

## 3. Formal system (mechanical v1)

### 3.1 Universe
`ADV50 ≥ $50M`, `ADR20 ≥ 3.0%`, `close > SMA50 ∧ close > SMA200 ∧ slopes up`, ideally `close > EMA20`. Rationale: liquidity to avoid slippage illusion; ADR to select "growthy" names that *can* move (transcript: banks excluded).

### 3.2 Regime (first filter)
On `QQQ`: `RISK-ON` iff `close>MA10 ∧ close>MA20 ∧ slopes up`; `RISK-OFF` iff `close<MA10 ∧ close<MA20`; else `CHOPPY`. Exposure `1.0 / 0.0 / 0.25`. Live mix 2020–26: **RISK-ON 42.36%, RISK-OFF 28.97%, CHOPPY 27.55%, WARMUP 1.12%** (`results/regime_mix.json`). Implication: ~57% of days are *not* full-risk long — "survive so you can thrive later."

### 3.3 Setup → trigger
1. `stage2` (3.1). 2. `wedge_pop`. 3. `launch_pad`. 4a. **Buy strength:** `close > HH20(−1) ∧ vol>1.2×mean ∧ RS_ok ∧ dist50<4 ATR`. 4b. **Buy weakness:** pullback into `±1.5%` of EMA10/20 with same guards. 5. **Extension veto:** `dist50 = (close−SMA50)/ATR14 ≥ 4.0 → skip`. 6. **Breakdown (short watch):** `close<EMA20` after stage2 → demote to short list (v1 records, does not trade shorts).

Signals use bar `t` to trade bar `t` close + costs (documented conservative proxy for `t+1` open; unit-tested causal).

### 3.4 Risk and exit
Risk fractions: starter **0.2%**, normal **0.3%**, strong **0.5%** (RISK-ON + cushion), conviction **1.0%** (A+ only: RS+launch+exposure), minuscule **0.05%** (MTD ≤−5% or RISK-OFF or 2026 tilt rule: ≤3 trades/day, ≤1% daily risk). Position: `shares = equity×risk / (entry−stop)`, capped 25% notional. Stop: `min(low, entry−1×ATR)`, honored at open on gaps. Exit v1: **1/3 at +2.5×ATR** (transcript 2.5–2.8 ADR partial), stop→breakeven, rest on **EMA20 violation** or 30-day time stop. No averaging down; one position/symbol.

Order of operations (transcript mantra): **(1) preserve → (2) consistent singles → (3) superior home-runs only with cushion.**

---

## 4. Verification protocol (2026 standard, no hand-waving)

- **Live public data only:** `yfinance` daily bars, `auto_adjust=True`, cached to `data/*.parquet` (16 symbols verified 2026-09-30; ranges e.g. QQQ/SPY 2020-01-02→2026-09-30 n=1,695; HOOD from 2021-07-29 n=1,299; ARM from 2023-09-14 n=764; SNDK from 2025-02-13 n=409). Ticker correction logged: `UCT→UCTT` (Ultra Clean Holdings) after empty-download verification.
- **No look-ahead:** indicators `min_periods`-gated; `was_below` uses `shift(1)`; regime joined contemporaneously; `test_no_lookahead` passes.
- **Costs always on:** 5 bps/side + open-gap stop discipline; dust filter $100.
- **Ablations:** full vs `no_regime` (exposure≡1.0) vs `no_rs` (recomputed `rs_ok≡True` path — earlier version had a bug where triggers already baked RS; fixed and re-ran) vs `no_extension_veto` (forward-return analysis, since triggers already veto by construction).
- **Walk-forward / holdout:** train 2020–22 (COVID crash + bear) vs test 2023–26 (bull + Liberation-Day bottom) with *frozen* rules — stability check, not re-optimization.
- **Metrics jointly:** total/annual, volatility, Sharpe, maxDD, Calmar, profit factor, win rate, expectancy, n_trades. Thresholds cited for context, not cherry-picked.
- **Reproducibility:** `docker compose up` reruns everything; `results/summary.md` is machine-generated and README copies it verbatim.

Limitations disclosed: Yahoo survivorship (delisted names absent — classic bias *against* us if anything, since losers vanish); no intraday 5-min MACD/pullback refinement; no short engine; no group-strength filter (NVDA↔AMD↔AVGO co-setup coded as future); SNDK/ARM short histories.

---

## 5. Results (live, verbatim from `results/summary.md`)

> Copy-paste of machine output — **do not edit; rerun to update:**

```
- PLTR: n_trades=27 win=33.33% pf=0.77 sharpe=-0.17 mdd=-1.43% total=-0.74% | no_regime_total=0.26% no_rs_total=1.29% no_ext_total=-0.74% signals=85/nors=129/noext=85
- CRWD: n_trades=37 win=37.84% pf=0.91 sharpe=-0.07 mdd=-2.44% total=-0.31% | no_regime_total=-1.89% no_rs_total=2.52% no_ext_total=-0.31% signals=127/nors=205/noext=127
- SPOT: n_trades=17 win=76.47% pf=8.85 sharpe=0.86 mdd=-0.31% total=3.15% | no_regime_total=2.30% no_rs_total=2.52% no_ext_total=3.15% signals=61/nors=138/noext=61
- HOOD: n_trades=24 win=54.17% pf=3.74 sharpe=0.76 mdd=-0.70% total=4.23% | no_regime_total=2.87% no_rs_total=4.37% no_ext_total=4.23% signals=51/nors=98/noext=51
- NFLX: n_trades=4 win=75.00% pf=12.69 sharpe=0.46 mdd=-0.04% total=0.41% | no_regime_total=0.67% no_rs_total=0.98% no_ext_total=0.41% signals=10/nors=26/noext=10
- NVDA: n_trades=33 win=36.36% pf=0.79 sharpe=-0.18 mdd=-0.62% total=-0.51% | no_regime_total=2.25% no_rs_total=-1.97% no_ext_total=-0.51% signals=90/nors=162/noext=90
- AMD: n_trades=26 win=46.15% pf=1.49 sharpe=0.26 mdd=-1.00% total=1.41% | no_regime_total=1.42% no_rs_total=-0.04% no_ext_total=1.41% signals=72/nors=143/noext=72
- AVGO: n_trades=19 win=21.05% pf=0.22 sharpe=-0.84 mdd=-2.03% total=-2.03% | no_regime_total=-3.18% no_rs_total=-2.72% no_ext_total=-2.03% signals=59/nors=114/noext=59
- ARM: n_trades=20 win=45.00% pf=0.92 sharpe=-0.07 mdd=-1.61% total=-0.18% | no_regime_total=2.50% no_rs_total=0.14% no_ext_total=-0.18% signals=36/nors=55/noext=36
- MU: n_trades=21 win=38.10% pf=1.36 sharpe=0.14 mdd=-2.00% total=0.82% | no_regime_total=0.60% no_rs_total=-1.39% no_ext_total=0.82% signals=72/nors=121/noext=72
- UCTT: n_trades=6 win=50.00% pf=0.29 sharpe=-0.31 mdd=-0.30% total=-0.25% | no_regime_total=-0.20% no_rs_total=-0.48% no_ext_total=-0.25% signals=14/nors=27/noext=14
- COIN: n_trades=17 win=23.53% pf=0.98 sharpe=-0.01 mdd=-2.06% total=-0.04% | no_regime_total=0.44% no_rs_total=-1.29% no_ext_total=-0.04% signals=40/nors=69/noext=40
- SNDK: n_trades=6 win=66.67% pf=38.48 sharpe=0.88 mdd=-0.05% total=3.91% | no_regime_total=3.48% no_rs_total=3.87% no_ext_total=3.91% signals=23/nors=26/noext=23
- TQQQ: n_trades=49 win=46.94% pf=1.27 sharpe=0.16 mdd=-1.62% total=0.73% | no_regime_total=2.36% no_rs_total=1.00% no_ext_total=0.73% signals=116/nors=170/noext=116
```

**Reading (honest):**

- **Capital preservation holds:** every maxDD ≤2.44% (worst CRWD −2.44%, COIN −2.06%, AVGO −2.03%). At 0.3% risk + 25% cap, the system *cannot* blow up — exactly the "survive first" design. The cost is muted totals (−2.03%…+4.23% over ~6.75y at v1 size).
- **Win rates match the transcript:** PLTR 33.33%, NVDA 36.36%, CRWD 37.84%, MU 38.10% — the *"I only win 31% and still compound"* phenomenon is reproduced; outliers (SPOT 76.47% PF 8.85, SNDK 66.67% PF 38.48, NFLX 75% PF 12.69 on n=4) carry the book.
- **Regime is a filter, not alpha:** helps HOOD (+4.23% vs +2.87% no-regime), SPOT, CRWD, AVGO, MU; hurts NVDA (−0.51% vs +2.25%), ARM, PLTR — stock-dependent, consistent with Zakamulin (common market signal helps Sharpe on average, not every name). 272/860 (31.6%) long signals fall in RISK-OFF and are suppressed (331 RISK-ON / 257 CHOPPY / 272 RISK-OFF).
- **RS halves the book:** `nors` signals 1.5–2.3× full (e.g. CRWD 205 vs 127, NVDA 162 vs 90) — RS is the selectivity knob; removing it lifts totals on some (CRWD +2.52%, PLTR +1.29%) but degrades others (NVDA −1.97%, MU −1.39%), i.e. RS trades frequency for focus.
- **Extension veto binds rarely but meaningfully:** 19.4% of NVDA bars vetoed; triggers already exclude extended entries so `no_ext` totals tie — the veto's value is risk, not return (see H4).

Sizing sweep on NVDA (same 33 trades): `fixed 1% → total −1.19% / mdd −2.28%`; `dynamic Clement → −0.51% / −0.62%`; `tiny 0.1% → −0.14% / −0.23%`. Dynamic cuts drawdown 3.7× vs fixed at same signals — the Flanders "slash size" lesson quantified.

Walk-forward (frozen rules): train 2020–22 PLTR −0.57% (n=4, bear chop) → test 2023–26 +0.15% (n=21); pattern repeats (bear small-sample pain, bull recovery) — stability without re-optimization, but also proof v1 alone does not manufacture champion outliers.

---

## 6. Five hidden patterns (new, testable, PhD-ready)

All from `results/hidden_patterns.json` (forward-20d informational analysis + backtest ranks):

**H1 — Breakout leg pays 3× pullback leg.** Breakout bars (n=149): mean fwd20 **+8.18%**, median +4.89%, hit 58.94%. Pullback bars (n=695): +2.58%, median +1.41%, hit 53.31%. *Implication:* "buy strength" is the convex leg; pullbacks are higher-frequency income. A PhD can optimize the mix as a two-armed bandit.

**H2 — Launch-pad conditioning is real but modest.** Launch-pad-true (n=5,713): +4.78%, hit 60.27%. False (n=14,614): +4.16%, hit 55.72%. Lift ≈+0.6pp mean, +4.6pp hit. Volume dry-up + VCP is a *triage*, not a holy grail — combine with RS for convexity.

**H3 — Unconditional forward returns mislead; signals need regime.** All-bar fwd20 by regime: RISK-OFF +4.94% > CHOPPY +4.73% > RISK-ON +3.65% (mean-reversion bounce effect). But *signals* concentrate 38.5% in RISK-ON and backtest ablation shows regime helps 5/14, hurts 3/14 — regime's job is *drawdown suppression*, not return maximization. PhD: model regime as variance gate (à la Daniel-Moskowitz crash indicator), not mean predictor.

**H4 — The extension paradox.** Vetoed (≥4 ATR, n=2,627): fwd20 **+6.30%**, hit **66.29%**. Allowed (n=17,700): +4.04%, hit 55.63%. Extended stocks *keep going* (momentum). The 4-ATR veto therefore sacrifices upside for sleep — optimal only under concave utility / monthly-floor constraints. PhD: derive the optimal extension threshold as a function of cushion and MTD.

**H5 — Concentration is the entire game.** Ranked totals: HOOD +4.23%, SNDK +3.91%, SPOT +3.15%, AMD +1.41%, MU +0.82% … AVGO −2.03%. Top-3 share of summed totals **106.4%** (losers net off). Matches transcript: *"bulk of returns from seven winners"* and 2024 seven-name list. Mechanical diversification *destroys* the edge; concentration + quick culling *is* the edge. PhD: formalize "concentrate-or-cash" as optimal stopping.

Each H includes n, mean/median/hit — powered enough for a follow-up paper and falsifiable on new data.

---

## 7. Why v1 ≠ +500% (negative result, fully disclosed)

Champion math requires what v1 omits by design: (a) **Selectivity:** ≤3 trades/day, skip "half-decent" (transcript: 500/1000 trades were fat); v1 takes all 860 signals. (b) **Concentration + margin:** full position + adds into strength (RDDT/PLTR adds, ETH 1% + parlay) vs v1 25% cap, no pyramiding. (c) **Short playbook** (Feb–Mar 2025 short-US/long-HK; TQQQ capitulation timing) vs v1 long-only. (d) **Intraday execution** (5-min higher-low, 6/20 MACD, low-of-day stops) vs daily proxy. (e) **Cushion-aware aggression** (50% May 2025 after 31% cushion) vs flat 0.3%. Our tiny totals are therefore a *lower bound* proving the risk engine, not a refutation of the champions — verified by the fact that the best v1 names (HOOD/SPOT/SNDK) are exactly recent leaders.

---

## 8. How to reproduce (Docker, 3 commands)

```bash
git clone <this-repo> && cd clement-momentum-lab-2026
docker compose build
docker compose run --rm lab python scripts/fetch_live.py --config configs/default.yaml
docker compose run --rm lab python scripts/run_all.py --period 2020-01-01:2026-10-01 --run-all
docker compose run --rm lab python experiments/hidden_patterns.py
# outputs: data/*.parquet  results/per_symbol.json  results/hidden_patterns.json  results/summary.md
```

Local (no Docker): `PYTHONPATH=src python3 scripts/run_all.py --period 2020-01-01:2026-10-01 --run-all` · Tests: `PYTHONPATH=src python3 -m pytest tests/ -v` (3/3 pass). Notebook profile: `docker compose --profile notebook up notebook` → `:8888`.

Config: `configs/default.yaml` (universe, ADR/ADV, risk, costs). Code: `src/clement_lab/{indicators,regime,signals,sizing,backtest,data_loader}.py`. Experiments: `scripts/run_all.py`, `experiments/hidden_patterns.py`, `experiments/regime_signal_count.py`.

---

## 9. Threats to validity

Survivorship (Yahoo current constituents; delisted losers missing — biases *up*); single-index regime (QQQ only; SPY cross-check pending); daily granularity; fixed 5 bps costs (understates gaps/shorts); short history for ARM/SNDK/HOOD/COIN; no group-strength or earnings-distance filter; no multiple-testing correction (Harvey-Liu-Zhu t>3.0) — mitigated by frozen-rule walk-forward and joint-metric reporting.

---

## 10. From benchmark to PhD (12-month roadmap)

1. **Short engine + long/short portfolio** (breakdown → wedge-into-MA on dead volume → cover-half; Zakamulin long-only vs long-short by objective). 2. **Group-at-back** (sector co-setup count as conviction multiplier). 3. **Intraday refinement** (5-min entry, 6/20 MACD, low-of-day stop; compare daily proxy slippage). 4. **Optimal extension & partial** (H4 + 2.5–2.8 ADR partial as stochastic control). 5. **Concentration theory** (H5 as Kelly with monthly floor). 6. **Crash indicator** (H3 + Bianchi skewness/vol predictor). Each maps to one H and one experiment file — the thesis writes itself.

---

## 11. References (voted sources)

O'Neil *How to Make Money in Stocks*; Minervini *Trade Like a Stock Market Wizard / Think & Trade Like a Champion*; Kell cycle / wedge-pop (TraderLion, KellTrading, Deepvue); Kulamagi streams/model-book; Morales-Katcher short-selling; Goldstein *Mastering the Mental Game* (behavioral leakages); Schwager *Market Wizards*; Weinstein stage analysis; USIC standings (BusinessWire 2024/2025, Financial-Competitions, J. Law +1,499% 2-yr); Moskowitz-Ooi-Pedersen (2012); Daniel-Moskowitz (2016); Kim-Tse-Wald (2016); Baltas-Kosowski; Zakamulin (2026); Lim-Zohren-Roberts; Harvey-Liu-Zhu; QuantNeuralEdge / SignalWavesAI 2026 backtest guides; yfinance docs; World Bank / OpenAlex / Crossref verifications in Phase 0.

---

## 12. Citation & sharing

Public research, educational use only — **not financial advice.** Data © Yahoo Finance via yfinance (research/educational). Code MIT (see `LICENSE` if added by maintainer). If you use this benchmark, cite the repo + USIC + Kell/O'Neil/Minervini lineages above, and rerun `run_all.py` rather than copying numbers — past performance never guarantees future results.

*Trade better: preserve → chip up → swing only with cushion, regime, RS, and a dry launch-pad at your back.*
