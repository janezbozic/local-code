# Sandbox boundary and platform backends

## Contract

OpenCode, llama.cpp, and document conversion must allow loopback networking and
deny non-loopback IP destinations. `make check`, preflight, and `make test` run
a behavioral probe that fails closed if either side of that contract fails.

Search (SearXNG + gateway) intentionally crosses the external boundary and is
not wrapped by this jail.

## macOS backend

Processes run under `sandbox-exec` Seatbelt profiles in `config/firewall/*.sb`.
`sandbox-exec` is deprecated by Apple. Availability and observed behavior remain
startup prerequisites on macOS.

## Linux backend (Milestone 7)

**Status:** implemented in-tree; not a fully accepted publish path until
[LINUX_ACCEPTANCE.md](../benchmarks/LINUX_ACCEPTANCE.md) is completed on a real
host. macOS remains the proven platform.

Linux uses `tools/sandbox/run.sh`, which executes:

```sh
systemd-run --user --collect \
  --property=IPAddressDeny=any \
  --property=IPAddressAllow=127.0.0.0/8 \
  --property=IPAddressAllow=::1 \
  -- <command>
```

Host loopback stays shared so OpenCode can reach `127.0.0.1:8080` / `8890`.
This is process-scoped and does **not** install a long-running systemd service,
login item, or auto-restart unit. Details:
[config/firewall/linux/README.md](../config/firewall/linux/README.md).

## WSL2 (Milestone 8)

WSL2 guests report as Linux and use the same systemd-run IP filter backend.
Native Windows is unsupported. Requirements: WSL2 (not WSL1), systemd enabled
in `/etc/wsl.conf`, and a working `systemd-run --user` session. Probe output
labels the backend `systemd-run-ipfilter/wsl`. See
[MILESTONE_8_APPROVALS.md](MILESTONE_8_APPROVALS.md) and
[WSL2_ACCEPTANCE.md](../benchmarks/WSL2_ACCEPTANCE.md).

## Operator expectations

1. Re-run `make check` after OS upgrades before trusting the workbench.
2. If the probe fails, stop using the workbench until the platform backend is
   repaired.
3. Keep application policy (OpenCode permissions, loopback binds, PID stop
   validation) even when the OS jail is healthy.

## Proof commands

```sh
make check
make network-audit
python3 tools/sandbox-probe.py --profile opencode
python3 tools/sandbox-probe.py --profile llama
python3 tools/sandbox-probe.py --profile documents
```
