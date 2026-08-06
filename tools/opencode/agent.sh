#!/bin/zsh

set -eu

script_dir="${0:A:h}"
source "${script_dir}/../common.sh"
root="$(repo_root)"
profile="${MODEL_PROFILE:-gpt-oss}"
case "${profile}" in
  coder) model_id="qwen2.5-coder-7b" ;;
  granite) model_id="granite-4.1-8b" ;;
  gpt-oss) model_id="gpt-oss-20b" ;;
  qwen36) model_id="qwen3.6-27b" ;;
  *) die "unknown MODEL_PROFILE '${profile}'; choose coder, granite, gpt-oss, or qwen36" ;;
esac
opencode_bin="${OPENCODE_BIN:-${root}/.tools/opencode-v1/node_modules/.bin/opencode}"
rg_bin="${RG_BIN:-$(command -v rg 2>/dev/null || true)}"
if [[ -z "${rg_bin}" || ! -x "${rg_bin}" ]]; then
  for candidate in \
    /opt/homebrew/bin/rg \
    /usr/local/bin/rg; do
    if [[ -x "${candidate}" ]]; then
      rg_bin="${candidate}"
      break
    fi
  done
fi
if [[ -z "${rg_bin}" || ! -x "${rg_bin}" ]]; then
  rg_bin="$(/usr/bin/find "${HOME}/.vscode/extensions" \
    -path '*/openai.chatgpt-*/bin/macos-aarch64/rg' \
    -type f -perm -111 -print -quit 2>/dev/null || true)"
fi
if [[ -n "${rg_bin}" ]]; then
  rg_bin="${rg_bin:A}"
fi

[[ -n "${rg_bin}" && -x "${rg_bin}" ]] || die "ripgrep is not installed or executable; install rg locally before starting OpenCode"

OPENCODE_BIN="${opencode_bin}" RG_BIN="${rg_bin}" "${script_dir}/preflight.sh" >/dev/null

mkdir -p \
  "${root}/.runtime/opencode/config" \
  "${root}/.runtime/opencode/data" \
  "${root}/.runtime/opencode/state" \
  "${root}/.runtime/opencode/cache" \
  "${root}/.runtime/opencode/bin" \
  "${root}/.runtime/tmp"

# Expose a repository-owned, bounded rg guard to the clean environment. The
# guard invokes only the resolved local binary and prevents oversized searches
# from including ignored dependencies, runtime data, models, or private inputs.
/bin/ln -sf "${root}/tools/opencode/rg-capped.sh" "${root}/.runtime/opencode/bin/rg"

interface_flags=(--pure --mini)
model_flags=(--model "local-llama/${model_id}")
case "${1:-}" in
  completion|acp|mcp|attach|run|debug|providers|agent|upgrade|uninstall|serve|web|models|stats|export|import|github|pr|session|plugin|db)
    interface_flags=(--pure)
    ;;
esac
case "${1:-}" in
  completion|acp|mcp|attach|debug|providers|agent|upgrade|uninstall|serve|web|models|stats|export|import|github|pr|session|plugin|db)
    model_flags=()
    ;;
esac
for argument in "$@"; do
  case "${argument}" in
    --port|--port=*)
      # The official VS Code extension always supplies a server port. OpenCode
      # V1's normal TUI supports it, but its minimal interface does not.
      interface_flags=(--pure)
      break
      ;;
  esac
done

cd "${root}"
exec /usr/bin/sandbox-exec -f "${root}/config/firewall/opencode.sb" \
  /usr/bin/env -i \
  HOME="${HOME}" \
  USER="${USER:-local-user}" \
  LOGNAME="${LOGNAME:-${USER:-local-user}}" \
  SHELL="/bin/zsh" \
  TERM="${TERM:-xterm-256color}" \
  LANG="${LANG:-en_US.UTF-8}" \
  PATH="${root}/.runtime/opencode/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" \
  TMPDIR="${root}/.runtime/tmp" \
  XDG_CONFIG_HOME="${root}/.runtime/opencode/config" \
  XDG_DATA_HOME="${root}/.runtime/opencode/data" \
  XDG_STATE_HOME="${root}/.runtime/opencode/state" \
  XDG_CACHE_HOME="${root}/.runtime/opencode/cache" \
  OPENCODE_CONFIG="${root}/opencode.json" \
  OPENCODE_DISABLE_AUTOUPDATE=1 \
  OPENCODE_DISABLE_DEFAULT_PLUGINS=1 \
  OPENCODE_DISABLE_LSP_DOWNLOAD=1 \
  OPENCODE_DISABLE_MODELS_FETCH=1 \
  OPENCODE_DISABLE_CLAUDE_CODE=1 \
  OPENCODE_ENABLE_EXA=0 \
  OPENCODE_PURE=1 \
  LOCAL_RG_BIN="${rg_bin}" \
  "${opencode_bin}" "${interface_flags[@]}" "${model_flags[@]}" "$@"
