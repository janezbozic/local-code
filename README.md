# Local Code

Local Code is a privacy-first agent workbench for Apple Silicon Macs, with
Linux x86_64 scaffolding in-tree (acceptance pending host evidence). It runs
OpenCode V1 against local `llama.cpp` inference, places every normal runtime
behind a loopback-only network boundary, and adds optional restricted web
research and preserving document workflows.

The repository is designed for deliberate, manual operation: no hosted model
provider, automatic startup, background updater, telemetry service, or implicit
download is part of the normal workflow.

## What is included

- Exact-pinned `opencode-ai@1.18.13` with isolated project-local state.
- Metal (macOS) or CUDA/CPU (Linux) `llama.cpp` with one serialized inference slot.
- IBM Granite 4.1 8B as a selectable profile, gpt-oss-20b as the accepted
  default (128K context on macOS evidence), and provisional `coder` / Qwen3.6
  profiles that remain unaccepted until their tool-call and memory gates pass.
- Supervised `make up` / `make down` session lifecycle without login items or
  systemd services.
- Six bounded agent roles with one-level delegation and fail-closed permissions.
- Optional SearXNG research through a DLP-, SSRF-, redirect-, and size-limited
  localhost MCP gateway.
- PDF, DOCX, PPTX, and XLSX import into canonical Markdown, with preserving
  export and render workflows.
- Behavioral network probes for every sandbox profile, PID identity validation,
  checksums, and repeatable acceptance benchmarks.

## Platform and status

| Platform | Status | Notes |
|---|---|---|
| macOS / Apple Silicon | **Supported** | Proven path: Seatbelt, Metal, gpt-oss 128K evidence in `benchmarks/`. |
| Linux x86_64 | **Code-complete; acceptance pending** | Sandbox façade, CUDA/CPU preflight, and docs are in-tree. Do not advertise full Linux support until `OPENCODE_BINARY_SHA256_LINUX_X64` is filled and `benchmarks/*-linux.json` is recorded on a real host ([benchmarks/LINUX_ACCEPTANCE.md](benchmarks/LINUX_ACCEPTANCE.md)). |
| Windows | Not supported | Follow-up; WSL2 may reuse the Linux path later. |

Startup tests the active sandbox backend and fails closed if loopback access or
non-loopback denial does not behave as expected.

This repository is publishable as a **macOS-first** local workbench. Linux
scaffolding is ready for bring-up; production Linux claims wait on host
evidence. Provisional profiles (`coder`, Qwen3.6) remain unaccepted on every OS.

All seven milestones in [PLANS.md](PLANS.md) are implemented. Recorded macOS
benchmark results are available in [benchmarks](benchmarks/README.md).

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

Start the default coding session (background gpt-oss model + foreground agent):

```sh
make up
```

Stop recorded background services:

```sh
make down
```

Or start the model and agent separately. The default profile is `gpt-oss`:

```sh
make model-start
```

Start OpenCode in another terminal:

```sh
make agent
```

For Granite, both commands must use the same profile:

```sh
make model-start PROFILE=granite
make agent PROFILE=granite
```

```sh
make up PROFILE=granite
```

Qwen3.6 27B uses `PROFILE=qwen36`. Its 19.1 GB Q4_K_M file is not installed
automatically and has not passed this 24 GB Mac's memory and tool-call gates.

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

This project is licensed under the [GNU General Public License v3.0](LICENSE).
