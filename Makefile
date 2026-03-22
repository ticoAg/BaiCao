.DEFAULT_GOAL := help

RESOURCE := $(firstword $(MAKECMDGOALS))
CLI_ARGS := $(if $(MAKECMDGOALS),$(MAKECMDGOALS),help)

VALID_RESOURCES := help deps api web stack

.PHONY: help deps api web stack

help:
	@if [ -z "$(RESOURCE)" ] || [ "$(RESOURCE)" = "help" ]; then \
		python3 scripts/dev_runtime.py $(CLI_ARGS); \
	fi

deps api web stack:
	@python3 scripts/dev_runtime.py $(CLI_ARGS)

%:
	@if [ "$@" = "$(RESOURCE)" ] && [ -z "$(filter $(RESOURCE),$(VALID_RESOURCES))" ]; then \
		python3 scripts/dev_runtime.py $(CLI_ARGS); \
	fi
