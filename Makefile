.PHONY: test coverage clean

# Python interpreter
PYTHON = python3

# Directories
DOCS_DIR = documentation/coverage_reports

# Create documentation directory if it doesn't exist
$(shell mkdir -p $(DOCS_DIR))

# Get current timestamp for report naming
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

test:
	$(PYTHON) -m pytest tests/ -v

coverage:
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:$(DOCS_DIR)/coverage_$(TIMESTAMP)

clean:
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 