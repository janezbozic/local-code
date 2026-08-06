#!/usr/bin/env zsh

# Run a command under the platform network jail for a logical profile
# (opencode | llama | documents). macOS uses Seatbelt profiles; Linux uses
# systemd-run --user IP address filters that keep host loopback shared.

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"

usage() {
  die "usage: tools/sandbox/run.sh --profile opencode|llama|documents -- command [args...]"
}

profile_name=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || usage
      profile_name="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done
[[ -n "${profile_name}" ]] || usage
[[ $# -gt 0 ]] || usage

case "${profile_name}" in
  opencode|llama|documents) ;;
  *) die "unknown sandbox profile '${profile_name}'" ;;
esac

os="$(os_id)"
case "${os}" in
  darwin)
    seatbelt="$(seatbelt_profile_path "${root}" "${profile_name}")"
    [[ -f "${seatbelt}" ]] || die "missing Seatbelt profile: ${seatbelt}"
    exec /usr/bin/sandbox-exec -f "${seatbelt}" "$@"
    ;;
  linux)
    require_linux_user_systemd
    exec systemd-run --user --collect --quiet \
      --working-directory="${root}" \
      --property=IPAddressDeny=any \
      --property=IPAddressAllow=127.0.0.0/8 \
      --property=IPAddressAllow=::1 \
      -- "$@"
    ;;
esac
