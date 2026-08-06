#!/usr/bin/env zsh

# Supervised single-user session start: ensure the model is healthy, optionally
# start restricted search, then run the agent in the foreground. No login items
# or automatic restart are created.

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/llama/runtime.env"
export MODEL_PROFILE="${MODEL_PROFILE:-gpt-oss}"
cd "${root}"

wait_health() {
  local _
  for _ in {1..120}; do
    if curl --fail --silent "http://${LLAMA_HOST}:${LLAMA_PORT}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  die "model server did not become healthy on ${LLAMA_HOST}:${LLAMA_PORT}"
}

if curl --fail --silent "http://${LLAMA_HOST}:${LLAMA_PORT}/health" >/dev/null 2>&1; then
  print -- "model server already healthy on ${LLAMA_HOST}:${LLAMA_PORT}"
else
  if [[ -f "${root}/.runtime/pids/model.json" ]]; then
    die "stale model PID record present without a healthy server; run make down"
  fi
  print -- "starting model profile ${MODEL_PROFILE} in background"
  BACKGROUND=1 MODEL_PROFILE="${MODEL_PROFILE}" "${root}/tools/model/start.sh"
  wait_health
fi

if [[ "${SEARCH:-0}" == "1" ]]; then
  if ! curl --fail --silent "http://127.0.0.1:8890/health" >/dev/null 2>&1; then
    print -- "starting restricted search services"
    "${root}/tools/web/start.sh"
  else
    print -- "restricted search already healthy"
  fi
fi

print -- "starting OpenCode with profile ${MODEL_PROFILE}"
export MODEL_PROFILE
exec "${root}/tools/opencode/agent.sh" "$@"
