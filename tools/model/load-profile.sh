#!/usr/bin/env zsh

# shellcheck disable=SC2154
profile="${MODEL_PROFILE:-gpt-oss}"
case "${profile}" in
  coder|granite|gpt-oss|qwen36) ;;
  *) die "unknown model profile '${profile}'; choose coder, granite, gpt-oss, or qwen36" ;;
esac
profile_file="${root}/config/llama/profiles/${profile}.env"
[[ -f "${profile_file}" ]] || die "missing model profile: ${profile_file}"
# shellcheck disable=SC1090
source "${profile_file}"
