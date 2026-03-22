.DEFAULT_GOAL := help

ifeq ($(strip $(MAKECMDGOALS)),)

.PHONY: help

help:
	@python3 scripts/dev_runtime.py help

else

RESOURCE := $(firstword $(MAKECMDGOALS))
CLI_ARGS := $(MAKECMDGOALS)
EXTRA_GOALS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

.PHONY: $(MAKECMDGOALS)

$(eval $(RESOURCE):;@python3 scripts/dev_runtime.py $(CLI_ARGS))
$(foreach goal,$(EXTRA_GOALS),$(eval $(goal):;@:))

endif
