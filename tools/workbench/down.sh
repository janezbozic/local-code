#!/usr/bin/env zsh

# Supervised shutdown for the single-user workbench. Stops recorded search and
# model services when present; never creates or removes login items.

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
cd "${root}"

rc=0
if [[ -f "${root}/.runtime/pids/search.json" ]]; then
  "${root}/tools/web/stop.sh" || rc=$?
else
  print -- "no recorded search services"
fi

if [[ -f "${root}/.runtime/pids/model.json" ]]; then
  "${root}/tools/model/stop.sh" || rc=$?
else
  print -- "no recorded background model server"
fi

print -- "workbench down complete"
exit "${rc}"
