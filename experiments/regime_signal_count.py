import yaml
from clement_lab.data_loader import download
from clement_lab.regime import compute_regime
from clement_lab.signals import add_features, compute_signals
cfg=yaml.safe_load(open("configs/default.yaml"))
data=download(cfg["universe"]["leaders_2023_2025"]+[cfg["universe"]["index"]], cfg["period"]["start"], cfg["period"]["end"], use_cache=True)
idx=data[cfg["universe"]["index"]]
regime=compute_regime(idx)
for r in ["RISK-ON","CHOPPY","RISK-OFF","WARMUP"]:
    total=0
    for s in cfg["universe"]["leaders_2023_2025"]:
        if s not in data:
            continue
        feat=add_features(data[s], idx["Close"])
        sig=compute_signals(feat, 50_000_000, 3.0)
        rr=regime["regime"].reindex(sig.index, method="ffill")
        total+=int(((sig["long_signal"]) & (rr==r)).sum())
    print(r, total)
