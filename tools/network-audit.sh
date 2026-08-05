#!/bin/zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/common.sh"
root="$(repo_root)"
cd "${root}"

python3 tests/test_policy.py
python3 tools/sandbox-probe.py --profile config/firewall/opencode.sb

typeset -A expected
expected[8080]="llama-server"
expected[8888]="searx"
expected[8890]="tools/web/gateway.py"

for port in 8080 8888 8890; do
  listeners="$(/usr/sbin/lsof -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${listeners}" ]]; then
    print -- "listener detected on audited port ${port}:"
    print -- "${listeners}"
    if print -- "${listeners}" | awk 'NR > 1 {print $9}' | grep -Ev '^(127\.0\.0\.1|\[::1\]):' >/dev/null; then
      die "non-loopback listener detected on port ${port}"
    fi
    pid_lines="$(/usr/sbin/lsof -nP -t -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null | sort -u)"
    pid_count="$(print -- "${pid_lines}" | wc -l | tr -d ' ')"
    [[ "${pid_count}" == 1 ]] || die "expected one owner for listener ${port}"
    owner_pid="${pid_lines}"
    command_line="$(ps -p "${owner_pid}" -o command=)"
    [[ "${command_line}" == *"${expected[${port}]}"* ]] || die "unrecognized owner for listener ${port}: ${command_line}"
    print -- "owner PID ${owner_pid}: ${command_line}"
    parent_pid="$(ps -p "${owner_pid}" -o ppid= | tr -d ' ')"
    parent_command="$(ps -p "${parent_pid}" -o command= 2>/dev/null || true)"
    print -- "parent PID ${parent_pid}: ${parent_command:-<exited>}"
    if [[ "${port}" == 8080 ]]; then
      established="$(/usr/sbin/lsof -nP -a -p "${owner_pid}" -iTCP -sTCP:ESTABLISHED 2>/dev/null || true)"
      if print -- "${established}" | awk 'NR > 1 {print $9}' | grep -- '->' | grep -Ev -- '->(127\.0\.0\.1|\[::1\]):' >/dev/null; then
        die "model process has an unexpected external TCP connection"
      fi
    fi
  fi
done

if [[ -f .runtime/pids/model.json ]]; then
  pid="$(jq -r '.pid' .runtime/pids/model.json)"
  kill -0 "${pid}" 2>/dev/null || die "stale model PID record detected"
fi

if [[ -f .runtime/pids/search.json ]]; then
  python3 - .runtime/pids/search.json <<'PY'
import json, subprocess, sys
record = json.load(open(sys.argv[1]))
for service in record.get("services", []):
    pid = str(service["pid"])
    command = subprocess.check_output(["ps", "-p", pid, "-o", "command="], text=True).strip()
    started = subprocess.check_output(["ps", "-p", pid, "-o", "lstart="], text=True).strip()
    if service["marker"] not in command or started != service["start_time"]:
        raise SystemExit(f"stale or mismatched search PID record: {pid}")
PY
fi

for profile in config/firewall/opencode.sb config/firewall/llama.sb config/firewall/documents.sb; do
  /usr/bin/sandbox-exec -f "${profile}" /usr/bin/true || die "sandbox profile failed syntax probe: ${profile}"
done

print -- "Network audit passed for the complete local-workbench boundary."
