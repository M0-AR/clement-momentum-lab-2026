.PHONY: setup fetch verify test notebook clean
setup:
	docker compose build
fetch:
	docker compose run --rm lab python scripts/fetch_live.py --config configs/default.yaml
verify:
	docker compose run --rm lab python scripts/run_all.py --period 2020-01-01:2026-10-01 --run-all
	docker compose run --rm lab python experiments/hidden_patterns.py
test:
	PYTHONPATH=src python3 -m pytest tests/ -v
notebook:
	docker compose --profile notebook up notebook
clean:
	rm -rf results/*.json results/summary.md __pycache__ .pytest_cache
