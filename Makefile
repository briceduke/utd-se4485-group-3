.PHONY: help install install-downloader install-deployer dev-install run-downloader run-deployer clean venv

VENV_NAME ?= .venv

venv:
	python3 -m venv $(VENV_NAME)
	@echo "Virtual environment created at $(VENV_NAME)"
	@echo "Activate with: source $(VENV_NAME)/bin/activate"

install: venv
	. $(VENV_NAME)/bin/activate && pip install -e ./downloader
	. $(VENV_NAME)/bin/activate && pip install -e ./deployer
	@echo "Packages installed successfully"
	@echo "Test with: everfox-downloader --help"

dev-install: install
	. $(VENV_NAME)/bin/activate && pip install black isort

run-dl:
	. $(VENV_NAME)/bin/activate && PYTHONPATH=./downloader/src python -m src.cli --help

run-dp:
	. $(VENV_NAME)/bin/activate && PYTHONPATH=./deployer/src python -m src.cli --help

clean:
	rm -rf $(VENV_NAME)
	rm -rf downloader/*.egg-info
	rm -rf deployer/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete

help:
	@echo "Available commands:"
	@echo "  install              - Install both packages in development mode"
	@echo "  dev-install          - Install packages + development dependencies"
	@echo "  run-dl       		  - Run downloader directly (no installation needed)"
	@echo "  run-dp        		  - Run deployer directly (no installation needed)"
	@echo "  venv                 - Create virtual environment"
	@echo "  clean                - Remove virtual environment and build artifacts"
	@echo ""
	@echo "For development on a single utility:"
	@echo "  1. Run once: make dev-install"
	@echo "  2. Run after each change: make run-dl      # or run-dp"

.DEFAULT_GOAL := help
