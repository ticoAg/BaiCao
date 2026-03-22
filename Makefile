.DEFAULT_GOAL := help

RESOURCE := $(firstword $(MAKECMDGOALS))
ACTION := $(or $(word 2,$(MAKECMDGOALS)),help)

VALID_RESOURCES := help deps api web stack

.PHONY: help deps api web stack

help:
	@if [ -z "$(RESOURCE)" ] || [ "$(RESOURCE)" = "help" ]; then \
		python3 scripts/dev_runtime.py help; \
	fi

deps api web stack:
	@python3 scripts/dev_runtime.py $(RESOURCE) $(ACTION)

%:
	@if [ "$@" = "$(RESOURCE)" ] && [ -z "$(filter $(RESOURCE),$(VALID_RESOURCES))" ]; then \
		python3 scripts/dev_runtime.py $(RESOURCE) $(ACTION); \
	fi
