#!/bin/zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/common.sh"
root="$(repo_root)"
cd "${root}"

require_command python3
require_command jq
require_command shellcheck
require_command sandbox-exec

jq empty opencode.json
shellcheck -s bash -e SC1091 tools/*.sh tools/model/*.sh tools/opencode/*.sh tests/*.sh
python3 tests/test_policy.py
python3 tests/test_documentation.py
python3 tools/sandbox-probe.py --profile config/firewall/opencode.sb

for profile in config/firewall/*.sb; do
  sandbox-exec -f "${profile}" /usr/bin/true
done

print -- "Workbench checks passed."
