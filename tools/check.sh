#!/usr/bin/env zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/common.sh"
root="$(repo_root)"
cd "${root}"

require_command python3
require_command jq
require_command shellcheck
require_command zsh

os="$(os_id)"
warn_wsl_repo_path "${root}"
case "${os}" in
  darwin) require_command sandbox-exec ;;
  linux) require_linux_user_systemd ;;
esac

jq empty opencode.json
shellcheck -s bash -e SC1091 tools/*.sh tools/model/*.sh tools/opencode/*.sh tools/web/*.sh tools/workbench/*.sh tools/sandbox/*.sh tests/*.sh
python3 tests/test_policy.py
python3 tests/test_documentation.py

for profile in $(sandbox_profiles); do
  case "${os}" in
    darwin)
      seatbelt="$(seatbelt_profile_path "${root}" "${profile}")"
      sandbox-exec -f "${seatbelt}" /usr/bin/true
      ;;
    linux)
      "${root}/tools/sandbox/run.sh" --profile "${profile}" -- /bin/true
      ;;
  esac
  python3 tools/sandbox-probe.py --profile "${profile}"
done

print -- "Workbench checks passed."
