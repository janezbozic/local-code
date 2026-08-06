#!/usr/bin/env zsh

set -eu

repo_root() {
  local source_path="${ZSH_ARGZERO:A}"
  if [[ -z "${source_path}" || "${source_path}" == "zsh" || "${source_path}" == "-zsh" ]]; then
    source_path="${0:A}"
  fi
  local cursor="${source_path:h}"
  while [[ "${cursor}" != "/" ]]; do
    if [[ -f "${cursor}/Makefile" && -f "${cursor}/PLANS.md" ]]; then
      print -r -- "${cursor}"
      return 0
    fi
    cursor="${cursor:h}"
  done
  print -u2 -- "error: could not locate repository root"
  return 1
}

die() {
  print -u2 -- "error: $*"
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is not installed: $1"
}

assert_loopback() {
  [[ "$1" == "127.0.0.1" ]] || die "refusing non-loopback host: $1"
}

os_id() {
  case "$(uname -s)" in
    Darwin) print -r -- darwin ;;
    Linux) print -r -- linux ;;
    *) die "unsupported operating system: $(uname -s)" ;;
  esac
}

arch_id() {
  case "$(uname -m)" in
    arm64|aarch64) print -r -- arm64 ;;
    x86_64|amd64) print -r -- x64 ;;
    *) die "unsupported architecture: $(uname -m)" ;;
  esac
}

find_lsof() {
  if [[ -x /usr/bin/lsof ]]; then
    print -r -- /usr/bin/lsof
  elif [[ -x /usr/sbin/lsof ]]; then
    print -r -- /usr/sbin/lsof
  else
    command -v lsof
  fi
}

sha256_file() {
  local path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${path}" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${path}" | awk '{print $1}'
  else
    python3 - "${path}" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
  fi
}

sandbox_profiles() {
  print -r -- opencode
  print -r -- llama
  print -r -- documents
}

seatbelt_profile_path() {
  local root="$1"
  local name="$2"
  print -r -- "${root}/config/firewall/${name}.sb"
}
