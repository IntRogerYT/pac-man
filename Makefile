# Makefile for PAC-MAN

# Variables
PYTHON = python3
MAIN_SCRIPT = pac-man.py
CONFIG = config.json
VENV = .venv
VENV_PIP = $(VENV)/bin/pip
VENV_PYTHON = $(VENV)/bin/python
VENV_FLAKE8 = $(VENV)/bin/flake8
VENV_MYPY = $(VENV)/bin/mypy

all: install run

# Manage de Virutal Enviroment
$(VENV):
	@echo "\n[*] Creating virtual environment '$(VENV)'..."
	python3 -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip

# Install dependencies (flake8, mypy, etc.)
install: $(VENV)
	@$(VENV_PIP) install -r requirements.txt --quiet --disable-pip-version-check

# Run the main program
run: install
	$(VENV_PYTHON) $(MAIN_SCRIPT) $(CONFIG)

# Run in debug mode (pdb)
debug: install
	$(VENV_PYTHON) -m pdb $(MAIN_SCRIPT) $(CONFIG)

# Clean up cache and build files
clean:
	@echo "[*] Cleaning cache and build artifacts..."
	# 1. Delete Python and Mypy caches across the entire project
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +

	# 2. Delete the virtual environment
	@rm -rf $(VENV)
	
	# 3. Delete the maze output file
	@find . -type f -name "*.txt" ! -name "requirements.txt" ! -name "config.txt" -delete
	
	# 4. Delete pip package build artifacts
	@find . -type d -name "build" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type f -name "*.spec" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	
	@echo "[*] Clean complete!"

# Mandatory Linting Rule
lint: install
	@echo "[*] Running standard linting..."
	$(VENV_FLAKE8) . --exclude=$(VENV)
	$(VENV_MYPY) . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# Optional Strict Linting
lint-strict: install
	@echo "[*] Running strict linting..."
	$(VENV_FLAKE8) . --exclude=$(VENV)
	$(VENV_MYPY) . --strict

# Run unit tests
test: install
	@echo "[*] Running unit tests..."
	$(VENV_PYTHON) -m unittest discover -s tests -v

# Package the project for deployment
package: install
	@echo "\n[*] Running packaging script..."
	bash build.sh

# Rules
.PHONY: all install run debug clean lint lint-strict test