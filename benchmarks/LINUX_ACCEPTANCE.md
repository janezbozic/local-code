# Linux acceptance checklist

**Publish note:** Until this checklist is completed and the resulting pins plus
`benchmarks/*-linux.json` files are committed, the public project is
**macOS-first**. Linux is code-complete only.

Run on a real Linux x86_64 host after completing
[docs/MILESTONE_7_APPROVALS.md](../docs/MILESTONE_7_APPROVALS.md).

```sh
make check
make test
make network-audit
make down
make benchmark-gpt-oss
```

Expected artifacts:

- `OPENCODE_BINARY_SHA256_LINUX_X64` (or `_LINUX_ARM64`) set in `config/versions.env`
- `benchmarks/profiles-gpt-oss-linux.json` (or granite CPU smoke if using CPU backend)
- Probe lines mentioning `systemd-run-ipfilter`

Do not overwrite macOS `benchmarks/profiles-gpt-oss.json`. Commit Linux evidence
only after reviewing the JSON for private paths.
