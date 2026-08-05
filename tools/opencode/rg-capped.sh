#!/bin/zsh

set -u

real_rg="${LOCAL_RG_BIN:-}"
if [[ -z "${real_rg}" || ! -x "${real_rg}" ]]; then
  print -u2 -- "error: LOCAL_RG_BIN is missing or not executable"
  exit 127
fi

# OpenCode's preview glob tool supplies positive --glob rules that re-include
# gitignored paths. Keep local dependencies, runtime state, models, private
# originals, and generated output outside agent search results. Also bound rows
# independently of the model-selected limit so one tool result cannot overflow
# the model context.
exclusions=(
  '--glob=!**/.git/**'
  '--glob=!**/.tools/**'
  '--glob=!**/.runtime/**'
  '--glob=!**/models/**'
  '--glob=!**/knowledge/originals/**'
  '--glob=!**/output/**'
)
args=()
inserted=0
for arg in "$@"; do
  if [[ "${arg}" == "--" ]]; then
    args+=("${exclusions[@]}")
    inserted=1
  fi
  args+=("${arg}")
done
if (( ! inserted )); then
  args+=("${exclusions[@]}")
fi

"${real_rg}" "${args[@]}" | /usr/bin/awk 'NR <= 250 { print }'
# zsh populates the pipestatus array for the pipeline above.
# shellcheck disable=SC2154
exit_status="${pipestatus[1]}"

exit "${exit_status}"
