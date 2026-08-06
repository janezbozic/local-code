# Linux network isolation

Linux does not use Seatbelt `.sb` files. The workbench wraps OpenCode, llama.cpp,
and document tools through `tools/sandbox/run.sh`, which on Linux executes:

```sh
systemd-run --user --collect \
  --property=IPAddressDeny=any \
  --property=IPAddressAllow=127.0.0.0/8 \
  --property=IPAddressAllow=::1 \
  -- <command>
```

This keeps the host loopback shared (so OpenCode can reach `127.0.0.1:8080` /
`8890`) while denying non-loopback destinations. It is process-scoped and does
not install a long-running systemd service or login unit.

## Requirements

- systemd user session (typically systemd ≥ 245)
- `systemd-run --user` must succeed for the interactive user
- Behavioral probe via `python3 tools/sandbox-probe.py --profile opencode`

## Profiles

Logical profiles remain `opencode`, `llama`, and `documents`. On Linux they all
use the same IP filter properties; the names exist so call sites and audits stay
aligned with macOS.

Search (SearXNG + gateway) stays outside this jail, matching macOS.

## WSL2

WSL2 guests use this same backend. Enable systemd in `/etc/wsl.conf`, keep the
repository off `/mnt/c`, and follow
[docs/MILESTONE_8_APPROVALS.md](../../../docs/MILESTONE_8_APPROVALS.md). Native
Windows is unsupported.
