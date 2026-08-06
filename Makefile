SHELL := $(shell command -v zsh)
.DEFAULT_GOAL := help

.PHONY: help check test benchmark benchmark-profiles benchmark-coder benchmark-gpt-oss benchmark-qwen36 \
	model-start model-stop agent up down network-audit \
	search-start search-stop document-import document-export document-render

help:
	@echo "Fully local agent workbench"
	@echo "  make check"
	@echo "  make test"
	@echo "  make up [PROFILE=gpt-oss|granite|coder|qwen36] [SEARCH=1]"
	@echo "  make down"
	@echo "  make benchmark  # requires model server"
	@echo "  make benchmark-profiles  # requires port 8080 to be free"
	@echo "  make benchmark-coder  # provisional; structured tool-call gate currently failing"
	@echo "  make benchmark-gpt-oss  # profile acceptance gate"
	@echo "  make benchmark-qwen36  # provisional sequential gate"
	@echo "  make network-audit"
	@echo "  make model-start [PROFILE=gpt-oss|granite|coder|qwen36] [BACKGROUND=1]"
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
	@python3 ./tools/model/profile-benchmark.py --profile granite

benchmark-coder:
	@python3 ./tools/model/profile-benchmark.py --profile coder

benchmark-gpt-oss:
	@python3 ./tools/model/profile-benchmark.py --profile gpt-oss

benchmark-qwen36:
	@python3 ./tools/model/profile-benchmark.py --profile qwen36

model-start:
	@BACKGROUND="$(BACKGROUND)" MODEL_PROFILE="$(or $(PROFILE),gpt-oss)" ./tools/model/start.sh

model-stop:
	@./tools/model/stop.sh

agent:
	@MODEL_PROFILE="$(or $(PROFILE),gpt-oss)" ./tools/opencode/agent.sh

up:
	@SEARCH="$(SEARCH)" MODEL_PROFILE="$(or $(PROFILE),gpt-oss)" ./tools/workbench/up.sh

down:
	@./tools/workbench/down.sh

network-audit:
	@./tools/network-audit.sh

search-start:
	@./tools/web/start.sh

search-stop:
	@./tools/web/stop.sh

document-import:
	@test -n "$(FILE)" || { echo "usage: make document-import FILE=/absolute/path/to/file" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@./tools/sandbox/run.sh --profile documents -- ./.venv/documents/bin/python ./tools/documents/workflow.py import "$(FILE)"

document-export:
	@test -n "$(FILE)" -a -n "$(FORMAT)" || { echo "usage: make document-export FILE=knowledge/markdown/file.md FORMAT=pdf" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@./tools/sandbox/run.sh --profile documents -- ./.venv/documents/bin/python ./tools/documents/workflow.py export "$(FILE)" "$(FORMAT)"

document-render:
	@test -n "$(FILE)" || { echo "usage: make document-render FILE=output/file.pdf" >&2; exit 2; }
	@test -x ./.venv/documents/bin/python || { echo "error: document environment is not installed; see docs/DOCUMENTS.md" >&2; exit 2; }
	@./tools/sandbox/run.sh --profile documents -- ./.venv/documents/bin/python ./tools/documents/workflow.py render "$(FILE)"
