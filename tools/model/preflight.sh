#!/bin/zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/llama/runtime.env"
source "${root}/config/versions.env"
source "${script_dir}/load-profile.sh"

assert_loopback "${LLAMA_HOST}"
[[ "${LLAMA_PARALLEL}" == "1" ]] || die "Milestone 1 permits exactly one inference slot"
[[ -x "${root}/${LLAMA_SERVER}" ]] || die "llama-server is not installed at ${LLAMA_SERVER}; review docs/MILESTONE_2_APPROVALS.md"
[[ -f "${root}/${LLAMA_BUILD_CACHE}" ]] || die "missing llama.cpp CMake cache: ${LLAMA_BUILD_CACHE}"
grep -Eq '^GGML_METAL:BOOL=ON$' "${root}/${LLAMA_BUILD_CACHE}" || die "llama.cpp build is not verified as Metal-enabled"
[[ -f "${root}/${LLAMA_MODEL}" ]] || die "model is not installed at ${LLAMA_MODEL}; review docs/MILESTONE_2_APPROVALS.md"

actual_sha="$(shasum -a 256 "${root}/${LLAMA_MODEL}" | awk '{print $1}')"
[[ "${actual_sha}" == "${LLAMA_MODEL_SHA256}" ]] || die "model SHA-256 mismatch for ${MODEL_PROFILE:-gpt-oss}"

if /usr/sbin/lsof -nP -iTCP:"${LLAMA_PORT}" -sTCP:LISTEN 2>/dev/null | grep -q .; then
  die "TCP port ${LLAMA_PORT} is already occupied"
fi

python3 "${root}/tools/sandbox-probe.py" --profile "${root}/config/firewall/llama.sb" >/dev/null
