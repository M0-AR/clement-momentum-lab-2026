"""Dynamic risk + progressive exposure (the "trade better" engine).

Transcript rules encoded:
- Normal risk 0.3% equity per trade; 0.5% when regime RISK-ON + cushion;
  1.0% only A+ conviction (all filters + group + volume + RS).
- Starter 0.2% when coming from cash / after drawdown.
- Max 3 positions/day, aggregate daily risk <=1% (2026 execution limit).
- Monthly floor: if MTD drawdown <= -5%, size -> minuscule (0.05%) until
  next A+ setup / equity makes new high. (Clement 5% rule + Flanders
  "slash size in half until insignificant".)
- Preserve (capital) -> Consistent (singles) -> Superior (home runs):
  need cushion before swinging. Implemented as cushion_gate.

All sizing returns FRACTION of equity to risk (not position notional).
Position shares = risk_frac * equity / (entry - stop).
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SizingConfig:
    normal_risk: float = 0.003
    strong_risk: float = 0.005
    conviction_risk: float = 0.01
    starter_risk: float = 0.002
    minuscule_risk: float = 0.0005
    monthly_floor: float = -0.05
    max_trades_per_day: int = 3
    max_daily_risk: float = 0.01


def select_risk(regime: str, has_cushion: bool, is_aplus: bool,
                mtd_return: float, cfg: SizingConfig = SizingConfig()) -> float:
    if mtd_return <= cfg.monthly_floor:
        return cfg.minuscule_risk
    if regime == "RISK-OFF":
        return cfg.minuscule_risk
    if regime == "CHOPPY":
        return cfg.starter_risk
    # RISK-ON
    if is_aplus and has_cushion:
        return cfg.conviction_risk
    if has_cushion:
        return cfg.strong_risk
    return cfg.normal_risk
