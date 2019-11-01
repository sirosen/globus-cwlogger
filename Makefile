.PHONY: help
help:
	@echo "These are our make targets and what they do."
	@echo ""
	@echo "  help:      Show this helptext"
	@echo ""
	@echo "  lint:      run linters and fixers"
	@echo ""
	@echo "  clean:     remove tooling virtualenv"

.venv:
	python3 -m venv .venv
	.venv/bin/pip install pre-commit==1.18.3

.PHONY: lint
lint: .venv
	.venv/bin/pre-commit run --all-files

.PHONY: clean
clean:
	rm -rf .venv
