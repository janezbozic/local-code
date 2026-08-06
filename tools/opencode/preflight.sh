#!/usr/bin/env zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/versions.env"
if [[ -f "${root}/config/llama/runtime.linux.env" ]] && [[ "$(os_id)" == linux ]]; then
  # shellcheck disable=SC1091
  source "${root}/config/llama/runtime.linux.env"
fi
opencode_bin="${OPENCODE_BIN:-${root}/.tools/opencode-v1/node_modules/.bin/opencode}"
package_json="${root}/.tools/opencode-v1/node_modules/opencode-ai/package.json"
rg_bin="${RG_BIN:-$(command -v rg || true)}"

[[ -x "${opencode_bin}" ]] || die "OpenCode V1 is not installed at ${opencode_bin}; review docs/MILESTONE_2_APPROVALS.md"
[[ -f "${package_json}" ]] || die "OpenCode package metadata is missing"
[[ -n "${rg_bin}" && -x "${rg_bin}" ]] || die "ripgrep is not installed or executable"
"${rg_bin}" --version >/dev/null || die "ripgrep failed its version probe"

installed_version="$(jq -r '.version' "${package_json}")"
[[ "${installed_version}" == "${OPENCODE_VERSION}" ]] || die "OpenCode version mismatch: expected ${OPENCODE_VERSION}, found ${installed_version}"

os="$(os_id)"
arch="$(arch_id)"
case "${os}-${arch}" in
  darwin-arm64) expected_sha="${OPENCODE_BINARY_SHA256_DARWIN_ARM64:-${OPENCODE_BINARY_SHA256:-}}" ;;
  linux-x64) expected_sha="${OPENCODE_BINARY_SHA256_LINUX_X64:-}" ;;
  linux-arm64) expected_sha="${OPENCODE_BINARY_SHA256_LINUX_ARM64:-}" ;;
  *) die "no OpenCode binary pin for ${os}/${arch}" ;;
esac
[[ -n "${expected_sha}" ]] || die "OpenCode binary SHA-256 pin is missing for ${os}/${arch}"

actual_sha="$(sha256_file "${opencode_bin}")"
[[ "${actual_sha}" == "${expected_sha}" ]] || die "OpenCode binary SHA-256 mismatch for ${os}/${arch}"

python3 "${root}/tools/sandbox-probe.py" --profile opencode >/dev/null
reported_version="$("${root}/tools/sandbox/run.sh" --profile opencode -- "${opencode_bin}" --version)"
[[ "${reported_version}" == *"${OPENCODE_VERSION}"* ]] || die "OpenCode executable reported an unexpected version: ${reported_version}"

print -- "OpenCode preflight passed: ${reported_version}; SHA-256 ${actual_sha}"
