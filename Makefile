PYTHON ?= python
.PHONY: data metrics test demo qa

data:
	$(PYTHON) scripts/download_telco.py
	$(PYTHON) scripts/download_retail.py
metrics:
	$(PYTHON) -m projects.churniq.src.pipeline
	$(PYTHON) -m projects.experimentlab.src.analysis
	$(PYTHON) -m projects.marketscope.src.warehouse
	$(PYTHON) -m projects.demandcast.src.forecast
test:
	$(PYTHON) -m pytest projects -q
qa:
	$(PYTHON) -m ruff check projects scripts --select E9,F63,F7,F82
	$(PYTHON) -m pytest projects -q
demo:
	$(PYTHON) -m http.server 8780 --bind 127.0.0.1 --directory docs
