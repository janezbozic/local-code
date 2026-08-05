#!/bin/zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/versions.env"
opencode_bin="${OPENCODE_BIN:-${root}/.tools/opencode-v1/node_modules/.bin/opencode}"
package_json="${root}/.tools/opencode-v1/node_modules/opencode-ai/package.json"
rg_bin="${RG_BIN:-$(command -v rg || true)}"

[[ -x "${opencode_bin}" ]] || die "OpenCode V1 is not installed at ${opencode_bin}; review docs/MILESTONE_2_APPROVALS.md"
[[ -f "${package_json}" ]] || die "OpenCode package metadata is missing"
[[ -n "${rg_bin}" && -x "${rg_bin}" ]] || die "ripgrep is not installed or executable"
"${rg_bin}" --version >/dev/null || die "ripgrep failed its version probe"

installed_version="$(jq -r '.version' "${package_json}")"
[[ "${installed_version}" == "${OPENCODE_VERSION}" ]] || die "OpenCode version mismatch: expected ${OPENCODE_VERSION}, found ${installed_version}"

actual_sha="$(shasum -a 256 "${opencode_bin}" | awk '{print $1}')"
[[ "${actual_sha}" == "${OPENCODE_BINARY_SHA256}" ]] || die "OpenCode binary SHA-256 mismatch"

python3 "${root}/tools/sandbox-probe.py" --profile "${root}/config/firewall/opencode.sb" >/dev/null
reported_version="$(/usr/bin/sandbox-exec -f "${root}/config/firewall/opencode.sb" "${opencode_bin}" --version)"
[[ "${reported_version}" == *"${OPENCODE_VERSION}"* ]] || die "OpenCode executable reported an unexpected version: ${reported_version}"

print -- "OpenCode preflight passed: ${reported_version}; SHA-256 ${actual_sha}"
