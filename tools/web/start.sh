#!/bin/zsh

set -eu
script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
source "${root}/config/web/runtime.env"
assert_loopback "${SEARXNG_HOST}"
assert_loopback "${WEB_GATEWAY_HOST}"

python_bin="${root}/${SEARCH_PYTHON}"
searxng_run="${root}/.venv/search/bin/searxng-run"
[[ -x "${python_bin}" ]] || die "SearXNG is not installed at ${SEARCH_PYTHON}; review docs/MILESTONE_3_APPROVALS.md"
[[ -x "${searxng_run}" ]] || die "SearXNG launcher is missing from the pinned search environment"

for port in "${SEARXNG_PORT}" "${WEB_GATEWAY_PORT}"; do
  if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    die "TCP port ${port} is already occupied"
  fi
done

mkdir -p "${root}/.runtime/pids" "${root}/.runtime/logs"
settings="${root}/config/searxng/settings.yml"
SEARXNG_SETTINGS_PATH="${settings}" \
  SEARXNG_BIND_ADDRESS="${SEARXNG_HOST}" \
  SEARXNG_PORT="${SEARXNG_PORT}" \
  "${searxng_run}" >"${root}/.runtime/logs/searxng.log" 2>&1 &
searx_pid=$!

"${python_bin}" "${root}/tools/web/gateway.py" \
  --host "${WEB_GATEWAY_HOST}" --port "${WEB_GATEWAY_PORT}" \
  >"${root}/.runtime/logs/web-gateway.log" 2>&1 &
gateway_pid=$!

cleanup() {
  kill "${gateway_pid}" "${searx_pid}" 2>/dev/null || true
  wait "${gateway_pid}" "${searx_pid}" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

for _ in {1..40}; do
  if ! kill -0 "${searx_pid}" 2>/dev/null || ! kill -0 "${gateway_pid}" 2>/dev/null; then
    die "search services exited during startup; inspect .runtime/logs"
  fi
  if curl --fail --silent "http://${WEB_GATEWAY_HOST}:${WEB_GATEWAY_PORT}/health" >/dev/null 2>&1 && \
     curl --fail --silent "http://${SEARXNG_HOST}:${SEARXNG_PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

curl --fail --silent "http://${WEB_GATEWAY_HOST}:${WEB_GATEWAY_PORT}/health" >/dev/null || die "web gateway health probe failed"
curl --fail --silent "http://${SEARXNG_HOST}:${SEARXNG_PORT}/" >/dev/null || die "SearXNG health probe failed"

python3 - "${root}/.runtime/pids/search.json" "${root}" \
  "${searx_pid}" "${gateway_pid}" "${python_bin}" "${settings}" <<'PY'
import datetime
import json
import pathlib
import subprocess
import sys

path, root, searx_pid, gateway_pid, python_bin, settings = sys.argv[1:]
services = []
for name, pid, marker in [
    ("searxng", int(searx_pid), "searxng-run"),
    ("web-gateway", int(gateway_pid), "tools/web/gateway.py"),
]:
    command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    started = subprocess.check_output(["ps", "-p", str(pid), "-o", "lstart="], text=True).strip()
    services.append({"name": name, "pid": pid, "start_time": started, "command": command, "marker": marker})
record = {
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "root": root,
    "python": python_bin,
    "settings": settings,
    "services": services,
}
pathlib.Path(path).write_text(json.dumps(record, indent=2) + "\n")
PY

trap - INT TERM EXIT
print -- "search services started: SearXNG PID ${searx_pid}, gateway PID ${gateway_pid}"
