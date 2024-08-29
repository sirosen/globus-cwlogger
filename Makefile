CLIENT_VERSION=$(shell grep 'version=' client/setup.py | grep -Eo '([[:digit:]]|\.)+')
DAEMON_VERSION=$(shell grep 'version=' daemon/setup.py | grep -Eo '([[:digit:]]|\.)+')

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

.PHONY: showvars tag-release prepare-release
showvars:
	@echo "VERSION=$(CLIENT_VERSION)"
	@echo "CLIENT_VERSION=$(CLIENT_VERSION)"
	@echo "DAEMON_VERSION=$(DAEMON_VERSION)"
prepare-release:
	tox -e prepare-release
tag-release:
	git tag -s "$(CLIENT_VERSION)" -m "v$(CLIENT_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(CLIENT_VERSION)
