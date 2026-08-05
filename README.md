# Local Code

Local Code is a privacy-first agent workbench for Apple Silicon Macs. It runs
OpenCode V1 against local `llama.cpp` inference, places every normal runtime
behind a loopback-only network boundary, and adds optional restricted web
research and preserving document workflows.

The repository is designed for deliberate, manual operation: no hosted model
provider, automatic startup, background updater, telemetry service, or implicit
download is part of the normal workflow.

## What is included

- Exact-pinned `opencode-ai@1.18.13` with isolated project-local state.
- Metal-enabled `llama.cpp` with one serialized inference slot.
- IBM Granite 4.1 8B as the default model and gpt-oss-20b as an optional profile.
- Six bounded agent roles with one-level delegation and fail-closed permissions.
- Optional SearXNG research through a DLP-, SSRF-, redirect-, and size-limited
  localhost MCP gateway.
- PDF, DOCX, PPTX, and XLSX import into canonical Markdown, with preserving
  export and render workflows.
- Behavioral network probes, PID identity validation, checksums, and repeatable
  acceptance benchmarks.

## Platform and status

The current implementation targets macOS on Apple Silicon and has been exercised
on a 24 GB Mac. It depends on Apple's deprecated `sandbox-exec`; startup tests
its actual behavior and fails closed if loopback access or non-loopback denial
does not behave as expected.

All six milestones in [PLANS.md](PLANS.md) are implemented. Recorded benchmark
results are available in [benchmarks](benchmarks/README.md).

## Quick start

This assumes the pinned CLI, `llama.cpp`, and at least one model have already
been installed. New installations should begin with
[docs/INSTALLATION.md](docs/INSTALLATION.md).

Run the repository checks:

```sh
make check
make test
make network-audit
```

Start the default Granite model in one terminal:

```sh
make model-start
```

Start OpenCode in another:

```sh
make agent
```

For gpt-oss, both commands must use the same profile:

```sh
make model-start PROFILE=gpt-oss
make agent PROFILE=gpt-oss
```

Stop foreground processes with `Ctrl-C`. Background model operation is
available with `make model-start BACKGROUND=1` and must be stopped using
`make model-stop`.

## Optional capabilities

Restricted web research:

```sh
make search-start
# use the local-safe-web tools from OpenCode
make search-stop
```

Document lifecycle:

```sh
make document-import FILE=/absolute/path/report.docx
make document-export FILE=knowledge/markdown/report.md FORMAT=pdf
make document-render FILE=output/report.pdf
```

Normal commands never install dependencies or download models. Installation
commands are separated into explicit approval documents.

## Security boundary

OpenCode receives a scrubbed environment, cannot load global OpenCode state,
uses only the provider at `127.0.0.1:8080`, and runs under a macOS profile that
denies non-loopback networking. The model server is bound to loopback and uses
one inference slot. Only the manually started SearXNG process and safe-fetch
gateway may access the public internet.

This is defense in depth, not a claim of perfect containment. Review the
[security model](config/firewall/README.md), [architecture](docs/ARCHITECTURE.md),
and [security policy](SECURITY.md) before processing sensitive material.

## Repository map

| Path | Purpose |
|---|---|
| `opencode.json` | Local provider, model, MCP, permission, and agent configuration |
| `config/` | Immutable pins, runtime profiles, SearXNG settings, and sandbox profiles |
| `tools/` | Lifecycle wrappers, audits, benchmarks, gateway, and document workflow |
| `agents/` | Agent-role and delegation documentation |
| `docs/` | Installation, operations, troubleshooting, and design documentation |
| `benchmarks/` | Tracked acceptance records; history remains ignored |
| `knowledge/` | Private originals, canonical Markdown, and manifests |
| `output/` | Derived documents and renders; ignored except for placeholders |
| `.tools/`, `.runtime/`, `models/` | Local toolchains, process state, logs, and model files; ignored |

## Documentation

Start with the [documentation index](docs/README.md). Key guides include:

- [Installation](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Manual operations](docs/OPERATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Document lifecycle](docs/DOCUMENTS.md)
- [VS Code notes](docs/VSCODE.md)
- [Contributing](CONTRIBUTING.md)

## License

No project license has been selected yet. Copyright remains with the repository
owner; publication does not grant permission to copy, modify, or redistribute
the project. Add an explicit license before inviting external reuse or
contributions.
