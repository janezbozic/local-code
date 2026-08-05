SHELL := /bin/zsh
.DEFAULT_GOAL := help

.PHONY: help check test benchmark benchmark-profiles benchmark-gpt-oss model-start model-stop agent network-audit \
	search-start search-stop document-import document-export document-render

help:
	@echo "Fully local agent workbench"
	@echo "  make check"
	@echo "  make test"
	@echo "  make benchmark  # requires model server"
	@echo "  make benchmark-profiles  # requires port 8080 to be free"
	@echo "  make benchmark-gpt-oss  # sequential 8K/16K acceptance"
	@echo "  make network-audit"
	@echo "  make model-start [PROFILE=granite|gpt-oss] [BACKGROUND=1]"
	@echo "  make model-stop"
	@echo "  make agent"
	@echo "  make search-start | make search-stop"
	@echo "  make document-import FILE=..."
	@echo "  make document-export FILE=... FORMAT=..."
	@echo "  make document-render FILE=..."

check:
	@./tools/check.sh

test:
	@./tests/run.sh

benchmark:
	@python3 ./tools/model/benchmark.py

benchmark-profiles:
	@python3 ./tools/model/profile-benchmark.py

benchmark-gpt-oss:
	@python3 ./tools/model/profile-benchmark.py --profile gpt-oss

model-start:
	@BACKGROUND="$(BACKGROUND)" MODEL_PROFILE="$(or $(PROFILE),granite)" ./tools/model/start.sh

model-stop:
	@./tools/model/stop.sh

agent:
	@MODEL_PROFILE="$(or $(PROFILE),granite)" ./tools/opencode/agent.sh

network-audit:
	@./tools/network-audit.sh

search-start:
	@./tools/web/start.sh

search-stop:
	@./tools/web/stop.sh

document-import:
	@test -n "$(FILE)" || { echo "usage: make document-import FILE=/absolute/path/to/file" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@/usr/bin/sandbox-exec -f config/firewall/documents.sb ./.venv/documents/bin/python ./tools/documents/workflow.py import "$(FILE)"

document-export:
	@test -n "$(FILE)" -a -n "$(FORMAT)" || { echo "usage: make document-export FILE=knowledge/markdown/file.md FORMAT=pdf" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@/usr/bin/sandbox-exec -f config/firewall/documents.sb ./.venv/documents/bin/python ./tools/documents/workflow.py export "$(FILE)" "$(FORMAT)"

document-render:
	@test -n "$(FILE)" || { echo "usage: make document-render FILE=output/file.pdf" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@/usr/bin/sandbox-exec -f config/firewall/documents.sb ./.venv/documents/bin/python ./tools/documents/workflow.py render "$(FILE)"
