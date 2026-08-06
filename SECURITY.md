# Security Policy

## Supported scope

The current main branch and the exact versions in `config/versions.env` are the
only supported configuration. **macOS on Apple Silicon is the supported publish
path.** Linux x86_64 and Windows via WSL2 scaffolding are in-tree but not fully
accepted until Linux binary pins and `benchmarks/*-linux.json` evidence are
recorded (see [benchmarks/LINUX_ACCEPTANCE.md](benchmarks/LINUX_ACCEPTANCE.md)
and [benchmarks/WSL2_ACCEPTANCE.md](benchmarks/WSL2_ACCEPTANCE.md)). Modified
sandbox backends, hosted providers, additional network bindings, parallel
inference, third-party extensions, unpinned upgrades, and native Windows
(cmd/PowerShell/Git Bash) are outside the supported security boundary.

## Reporting a vulnerability

Do not include private source code, documents, prompts, credentials, internal
paths, or identifying data in a public issue.

Use GitHub's private vulnerability reporting feature when it is enabled for the
repository. If it is not enabled, contact the repository owner privately and
provide only the minimum reproduction needed. A public issue is appropriate
for non-sensitive hardening suggestions that contain no exploit details or
private data.

Include:

- affected commit and component;
- OS and hardware version (macOS, Linux, or Windows+WSL2 distro);
- expected and observed boundary behavior;
- minimal reproduction steps;
- whether non-loopback traffic, credential exposure, unsafe overwrite, or PID
  misidentification occurred.

## Security expectations

- Never configure a hosted LLM provider.
- Never bind workbench services beyond `127.0.0.1`.
- Never publish `.runtime`, `.tools`, `.venv`, models, private originals, or
  generated output.
- Treat retrieved web content and model output as untrusted.
- Review all downloads, hashes, upgrades, and dependency changes explicitly.
- Preserve PID records and logs during incident investigation.

See [config/firewall/README.md](config/firewall/README.md) for the threat model
and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries.
