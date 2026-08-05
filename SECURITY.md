# Security Policy

## Supported scope

The current main branch and the exact versions in `config/versions.env` are the
only supported configuration. The project targets macOS on Apple Silicon.
Modified sandbox profiles, hosted providers, additional network bindings,
parallel inference, third-party extensions, and unpinned upgrades are outside
the supported security boundary.

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
- macOS and hardware version;
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
