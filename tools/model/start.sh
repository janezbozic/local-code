#!/usr/bin/env zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/llama/runtime.env"
source "${script_dir}/load-profile.sh"
"${script_dir}/preflight.sh"

mkdir -p "${root}/.runtime/pids" "${root}/.runtime/logs"
server="${root}/${LLAMA_SERVER}"
model="${root}/${LLAMA_MODEL}"
cd "${root}"
args=(
  --model "${model}"
  --host "${LLAMA_HOST}"
  --port "${LLAMA_PORT}"
  --ctx-size "${LLAMA_CONTEXT}"
  --parallel "${LLAMA_PARALLEL}"
  --n-gpu-layers "${LLAMA_GPU_LAYERS}"
  --jinja
)
sandbox=("${root}/tools/sandbox/run.sh" --profile llama --)

if [[ "${BACKGROUND:-}" == "1" ]]; then
  log_file="${root}/.runtime/logs/llama-server.log"
  "${sandbox[@]}" "${server}" "${args[@]}" >"${log_file}" 2>&1 &
  pid=$!
  sleep 1
  kill -0 "${pid}" 2>/dev/null || die "llama-server exited during startup; inspect ${log_file}"
  start_time="$(ps -p "${pid}" -o lstart= | sed 's/^ *//')"
  command_line="$(ps -p "${pid}" -o command=)"
  python3 - "${root}/.runtime/pids/model.json" "${pid}" "${start_time}" "${server}" "${command_line}" "${root}" "${LLAMA_HOST}" "${LLAMA_PORT}" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
record = {
    "pid": int(sys.argv[2]),
    "start_time": sys.argv[3],
    "executable": sys.argv[4],
    "command": sys.argv[5],
    "cwd": sys.argv[6],
    "host": sys.argv[7],
    "port": int(sys.argv[8]),
}
path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
PY
  print -- "llama-server started as PID ${pid}; stop with: make model-stop"
  exit 0
fi

print -- "Starting llama-server in the foreground on ${LLAMA_HOST}:${LLAMA_PORT}; stop with Ctrl-C."
print -- "Model profile: ${MODEL_PROFILE:-gpt-oss} (${LLAMA_MODEL_ID}, context ${LLAMA_CONTEXT})."
exec "${sandbox[@]}" "${server}" "${args[@]}"
