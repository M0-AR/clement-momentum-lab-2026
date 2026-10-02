"""Clement Lab package."""
from .indicators import ema, sma, atr, adr_percent
from .regime import compute_regime
from .signals import add_features, compute_signals
from .sizing import SizingConfig, select_risk
from .backtest import backtest_single, metrics_from_equity

__all__ = ["ema", "sma", "atr", "adr_percent", "compute_regime",
           "add_features", "compute_signals", "SizingConfig", "select_risk",
           "backtest_single", "metrics_from_equity"]
__version__ = "0.1.0"
