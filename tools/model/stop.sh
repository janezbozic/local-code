#!/usr/bin/env zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
pid_file="${root}/.runtime/pids/model.json"

if [[ ! -f "${pid_file}" ]]; then
  print -- "No recorded background model process. Foreground servers must be stopped with Ctrl-C."
  exit 0
fi

pid="$(jq -r '.pid' "${pid_file}")"
expected_start="$(jq -r '.start_time' "${pid_file}")"
expected_executable="$(jq -r '.executable' "${pid_file}")"
expected_cwd="$(jq -r '.cwd' "${pid_file}")"

[[ "${pid}" =~ ^[0-9]+$ ]] || die "invalid PID record"
if ! kill -0 "${pid}" 2>/dev/null; then
  die "recorded PID ${pid} is not running; remove ${pid_file} only after investigation"
fi

actual_start="$(ps -p "${pid}" -o lstart= | sed 's/^ *//')"
actual_command="$(ps -p "${pid}" -o command=)"
actual_cwd="$("$(find_lsof)" -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"

[[ "${actual_start}" == "${expected_start}" ]] || die "PID reuse detected; refusing to stop ${pid}"
[[ "${actual_command}" == *"${expected_executable}"* ]] || die "recorded process executable does not match"
[[ "${actual_cwd}" == "${expected_cwd}" ]] || die "recorded process working directory does not match"

kill -TERM "${pid}"
for _ in {1..50}; do
  if ! kill -0 "${pid}" 2>/dev/null; then
    rm -f "${pid_file}"
    print -- "Stopped llama-server PID ${pid}."
    exit 0
  fi
  sleep 0.1
done
die "llama-server did not stop after SIGTERM; PID record preserved"
