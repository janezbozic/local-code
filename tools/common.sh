#!/bin/zsh

set -eu

repo_root() {
  local source_path="${0:A}"
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

