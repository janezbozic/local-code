#!/usr/bin/env zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/llama/runtime.env"
if [[ -f "${root}/config/llama/runtime.linux.env" ]] && [[ "$(os_id)" == linux ]]; then
  # shellcheck disable=SC1091
  source "${root}/config/llama/runtime.linux.env"
fi
source "${root}/config/versions.env"
source "${script_dir}/load-profile.sh"

assert_loopback "${LLAMA_HOST}"
[[ "${LLAMA_PARALLEL}" == "1" ]] || die "Milestone 1 permits exactly one inference slot"
[[ -x "${root}/${LLAMA_SERVER}" ]] || die "llama-server is not installed at ${LLAMA_SERVER}; review docs/MILESTONE_2_APPROVALS.md or docs/MILESTONE_7_APPROVALS.md"
[[ -f "${root}/${LLAMA_BUILD_CACHE}" ]] || die "missing llama.cpp CMake cache: ${LLAMA_BUILD_CACHE}"

os="$(os_id)"
backend="${LLAMA_GPU_BACKEND:-}"
case "${os}" in
  darwin)
    grep -Eq '^GGML_METAL:BOOL=ON$' "${root}/${LLAMA_BUILD_CACHE}" || die "llama.cpp build is not verified as Metal-enabled"
    ;;
  linux)
    if [[ "${backend}" == cpu ]]; then
      print -- "Linux llama.cpp CPU backend selected via LLAMA_GPU_BACKEND=cpu"
    else
      grep -Eq '^GGML_CUDA:BOOL=ON$' "${root}/${LLAMA_BUILD_CACHE}" || die "llama.cpp build is not verified as CUDA-enabled; set LLAMA_GPU_BACKEND=cpu for CPU-only bring-up"
    fi
    ;;
esac

[[ -f "${root}/${LLAMA_MODEL}" ]] || die "model is not installed at ${LLAMA_MODEL}; review docs/MILESTONE_2_APPROVALS.md"

actual_sha="$(sha256_file "${root}/${LLAMA_MODEL}")"
[[ "${actual_sha}" == "${LLAMA_MODEL_SHA256}" ]] || die "model SHA-256 mismatch for ${MODEL_PROFILE:-gpt-oss}"

lsof_bin="$(find_lsof)"
if "${lsof_bin}" -nP -iTCP:"${LLAMA_PORT}" -sTCP:LISTEN 2>/dev/null | grep -q .; then
  die "TCP port ${LLAMA_PORT} is already occupied"
fi

python3 "${root}/tools/sandbox-probe.py" --profile llama >/dev/null
