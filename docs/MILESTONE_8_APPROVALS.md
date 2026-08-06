# Reviewed WSL2 installation notes (Milestone 8)

**Status:** code-complete as a Linux flavor; not a fully accepted publish path.
Native Windows (cmd, PowerShell, Git Bash, MSYS) remains unsupported. WSL2
reuses the Milestone 7 Linux sandbox, pins, and build recipes. Complete
[../benchmarks/WSL2_ACCEPTANCE.md](../benchmarks/WSL2_ACCEPTANCE.md) on a real
WSL2 guest before advertising production WSL support.

These steps contact Windows/WSL configuration and the same external download
hosts as Milestone 7. Review and approve each command. Normal workbench
operation never runs them.

## Supported WSL shape

- Windows 11 (or Windows 10 with a current WSL2 kernel) hosting an Ubuntu or
  similar systemd-capable distro
- WSL2 (not WSL1)
- systemd enabled for the distro (`systemd-run --user` must work)
- Repository cloned on a Linux filesystem (for example `~/projects/local-code`),
  not under `/mnt/c/...`
- Same packages and OpenCode/Linux llama pins as
  [MILESTONE_7_APPROVALS.md](MILESTONE_7_APPROVALS.md)
- First bring-up: `LLAMA_GPU_BACKEND=cpu`. CUDA is optional and requires
  NVIDIA Windows drivers plus a matching Linux CUDA toolkit inside WSL

## 1. Enable systemd in the WSL distro

Create or edit `/etc/wsl.conf` inside the Linux distro:

```ini
[boot]
systemd=true
```

From Windows PowerShell or cmd:

```bat
wsl --shutdown
```

Reopen the distro, then verify:

```sh
systemctl --user status
systemd-run --user --collect --quiet -- /bin/true
```

## 2. Install Linux packages and reviewed components

Follow [MILESTONE_7_APPROVALS.md](MILESTONE_7_APPROVALS.md) for apt packages,
OpenCode install, llama.cpp CUDA or CPU build, and model downloads. Fill
`OPENCODE_BINARY_SHA256_LINUX_X64` (or `_LINUX_ARM64`) the same way as bare
Linux—there is no separate WSL binary pin.

CPU bring-up example after sourcing Linux runtime defaults:

```sh
# Review config/llama/runtime.linux.env; prefer CPU for first WSL sessions.
export LLAMA_GPU_BACKEND=cpu
```

## 3. First-run verification

```sh
make check
make test
make network-audit
```

Sandbox probe lines on WSL should mention `systemd-run-ipfilter/wsl`.

## 4. Acceptance evidence

See [../benchmarks/WSL2_ACCEPTANCE.md](../benchmarks/WSL2_ACCEPTANCE.md). Record
`benchmarks/*-linux.json` (same suffix as bare Linux) and do not overwrite
macOS evidence.
