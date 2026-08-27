.PHONY: setup load part2 pipeline dashboard test check

PYTHON ?= python3
PORT ?= 8000

setup:
	$(PYTHON) -m pip install -r requirements.txt

load:
	$(PYTHON) load_data.py

part2:
	$(PYTHON) analyze_frequencies.py

pipeline: load part2
	mkdir -p docs/data
	cp relative-frequency.csv docs/data/relative-frequency.csv

dashboard:
	$(PYTHON) -m http.server $(PORT) --bind 0.0.0.0 --directory docs

test:
	$(PYTHON) -m pytest

check: test pipeline
