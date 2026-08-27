.PHONY: setup load part2 part3 part4 pipeline dashboard static-dashboard test check

PYTHON ?= python3
PORT ?= 8000

setup:
	$(PYTHON) -m pip install -r requirements.txt

load:
	$(PYTHON) load_data.py

part2:
	$(PYTHON) analyze_frequencies.py

part3:
	$(PYTHON) analyze_responders.py

part4:
	$(PYTHON) analyze_cohort.py

pipeline: load part2 part3 part4

dashboard:
	$(PYTHON) -m streamlit run streamlit_app.py

static-dashboard:
	$(PYTHON) -m http.server $(PORT) --bind 0.0.0.0 --directory docs

test:
	$(PYTHON) -m pytest

check: test pipeline
