#!/bin/zsh

set -eu
script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
record="${root}/.runtime/pids/search.json"
[[ -f "${record}" ]] || die "no recorded search services are running"

python3 - "${record}" <<'PY'
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

path = pathlib.Path(sys.argv[1])
record = json.loads(path.read_text())
validated = []
for service in record.get("services", []):
    pid = int(service["pid"])
    try:
        command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
        started = subprocess.check_output(["ps", "-p", str(pid), "-o", "lstart="], text=True).strip()
    except subprocess.CalledProcessError:
        continue
    if service["marker"] not in command or started != service["start_time"]:
        raise SystemExit(f"refusing to signal unrecognized PID {pid}")
    validated.append(pid)
for pid in validated:
    os.kill(pid, signal.SIGTERM)
deadline = time.monotonic() + 8
while validated and time.monotonic() < deadline:
    validated = [pid for pid in validated if pathlib.Path(f"/proc/{pid}").exists()] if sys.platform.startswith("linux") else [pid for pid in validated if subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0]
    time.sleep(0.1)
for pid in validated:
    raise SystemExit(f"PID {pid} did not stop cleanly")
path.unlink()
PY
print -- "recorded search services stopped"
