.PHONY: help
help:
	@echo "These are our make targets and what they do."
	@echo ""
	@echo "  help:      Show this helptext"
	@echo ""
	@echo "  autoformat:"
	@echo "             run autoformatting tools"
	@echo ""
	@echo "  lint:      run autoformatting tools as linters + flake8"
	@echo ""
	@echo "  clean:     remove tooling virtualenv"

.venv:
	python3 -m venv .venv
	.venv/bin/pip install black isort flake8
	touch .venv

.PHONY: autoformat
autoformat: .venv
	 .venv/bin/isort --recursive .
	 .venv/bin/black .

.PHONY: lint
lint: .venv
	.venv/bin/isort --check-only --recursive .
	.venv/bin/black --check .
	.venv/bin/flake8

.PHONY: clean
clean:
	rm -rf .venv
