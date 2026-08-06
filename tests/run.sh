#!/bin/zsh

set -eu

root="${0:A:h:h}"
cd "${root}"

python3 tests/test_policy.py
python3 tests/test_web_gateway.py
python3 tests/test_document_policy.py
python3 tools/sandbox-probe.py --profile config/firewall/opencode.sb

if [[ -x .venv/documents/bin/python ]]; then
  .venv/documents/bin/python tests/test_documents.py
else
  print -- "document environment not installed; lifecycle integration test skipped"
fi

make model-stop >/dev/null
[[ ! -e .runtime/pids/model.json ]] || { print -u2 -- "error: unexpected model PID record"; exit 1; }

print -- "Workbench tests passed."
