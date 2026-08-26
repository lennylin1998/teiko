.PHONY: setup pipeline

PYTHON ?= python

setup:
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) load_data.py
