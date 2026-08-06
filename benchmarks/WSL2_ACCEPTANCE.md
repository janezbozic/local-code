# WSL2 acceptance checklist

**Publish note:** Until this checklist is completed and Linux OpenCode pins plus
`benchmarks/*-linux.json` evidence are committed from a WSL2 guest (or bare
Linux), treat WSL2 as **code-complete only**. macOS remains the proven path.
Native Windows is unsupported.

Run inside a WSL2 distro with systemd enabled, after
[docs/MILESTONE_8_APPROVALS.md](../docs/MILESTONE_8_APPROVALS.md).

Prerequisites:

- `wsl.exe -l -v` shows version **2** for the distro
- Repository path is **not** under `/mnt/c` (prefer `~/projects/...`)
- `systemd-run --user --collect --quiet -- /bin/true` succeeds

```sh
make check
make test
make network-audit
make down
# Prefer CPU for first evidence unless CUDA was reviewed and built:
LLAMA_GPU_BACKEND=cpu make benchmark-gpt-oss
# or a smaller granite smoke if gpt-oss does not fit guest memory
```

Expected artifacts:

- `OPENCODE_BINARY_SHA256_LINUX_X64` (or `_LINUX_ARM64`) set in `config/versions.env`
- `benchmarks/profiles-gpt-oss-linux.json` (or granite CPU smoke)
- Probe lines mentioning `systemd-run-ipfilter/wsl`

Do not overwrite macOS `benchmarks/profiles-gpt-oss.json`. Commit evidence only
after reviewing JSON for private paths (including Windows usernames under
`/mnt/`).
