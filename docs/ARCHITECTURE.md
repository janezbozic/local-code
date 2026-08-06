# Architecture

## Overview

```text
                         optional internet access
                                  ▲
                                  │ validated requests only
                         ┌────────┴─────────┐
                         │ SearXNG :8888    │
                         │ safe MCP :8890   │
                         └────────▲─────────┘
                                  │ loopback
┌──────────────────┐     ┌────────┴─────────┐     ┌──────────────────┐
│ user / terminal  ├────►│ OpenCode V1      ├────►│ llama.cpp :8080  │
│ make targets     │     │ scrubbed +       │     │ Metal, 1 slot    │
└──────────────────┘     │ sandboxed        │     └──────────────────┘
                         └────────┬─────────┘
                                  │ scoped local tools
                    ┌─────────────┴─────────────┐
                    │ repository and documents │
                    └───────────────────────────┘
```

OpenCode, the model server, and document converters are denied non-loopback
networking by macOS sandbox profiles. Restricted search is a separate,
manually-started boundary: OpenCode talks only to the localhost gateway, while
the gateway validates requests before SearXNG or safe fetches reach the network.

## Components

### OpenCode

`tools/opencode/agent.sh` verifies the exact V1 binary and its SHA-256, resolves
a bounded `rg`, creates isolated XDG directories under `.runtime/opencode`,
scrubs inherited environment variables, disables updates/downloads/default
plugins, and executes OpenCode through `config/firewall/opencode.sb`.

`opencode.json` defines one local OpenAI-compatible provider, two selectable
model IDs, the optional localhost MCP server, six agents, compaction, watcher
exclusions, and fail-closed permissions.

### Local inference

`tools/model/start.sh` selects a profile, validates the model checksum and Metal
build, confirms that port 8080 is free, and starts `llama-server` on
`127.0.0.1:8080`. `LLAMA_PARALLEL=1` is a hard policy invariant.

| Profile | Model | Context | Role |
|---|---|---:|---|
| `gpt-oss` | gpt-oss-20b MXFP4 | 131,072 | Default, accepted |
| `granite` | Granite 4.1 8B Q4_K_M | 16,384 | Selectable accepted profile |
| `coder` | Qwen2.5 Coder 7B Instruct Q4_K_M | 16,384 | Provisional; tool-call gate failing |
| `qwen36` | Qwen3.6 27B Q4_K_M | 8,192 | Provisional; not accepted on 24 GB |

Always match the model server and agent profile. gpt-oss 128K acceptance evidence
is in `benchmarks/profiles-gpt-oss.json`.

Qwen3.6's GGUF metadata advertises a much larger native context, but this
workbench deliberately starts at 8K because the 19.1 GB quantized weights leave
limited memory headroom on the target machine.

### Restricted web research

`tools/web/start.sh` starts SearXNG on port 8888 and the MCP gateway on port
8890. The gateway provides `web_search`, `web_fetch`, `web_open`, and `web_find`.
It rejects secret-like queries, credentials in URLs, private/link-local targets,
unsafe redirects, excessive content, unsupported media, and likely prompt
injection. Retrieved content remains untrusted data.

### Documents

The document lifecycle is:

```text
original → extraction → canonical Markdown → export → render → inspection
```

Originals are copied into `knowledge/originals`; canonical Markdown and checksum
manifests are created separately; derived files go to `output`. Existing
canonical and derived files are never overwritten.

### Audits and tests

- `make check` validates static policy, shell scripts, JSON, and every sandbox.
- `make test` runs policy, gateway, sandbox, lifecycle, and optional document tests.
- `make network-audit` inspects listeners, owning processes, external model
  sockets, PID records, and sandbox syntax.
- Benchmark commands validate generation, tool calls, context, memory/swap,
  thermal observations, and clean unload behavior.

## Ports

| Port | Process | Exposure | Required |
|---:|---|---|---|
| 8080 | `llama-server` | `127.0.0.1` only | Core runtime |
| 8888 | SearXNG | `127.0.0.1` only | Optional research |
| 8890 | Safe MCP gateway | `127.0.0.1` only | Optional research |

Port 4096 is not part of the maintained runtime. It may be used by third-party
OpenCode UI extensions, which are outside this repository's security boundary.

## State and data ownership

| Location | Contents | Git policy |
|---|---|---|
| `.tools/` | Built binaries, source checkouts, wheel caches | Ignored |
| `.runtime/` | Logs, PID records, XDG state, temporary data | Ignored |
| `.venv/` | Optional Python environments | Ignored |
| `models/` | GGUF model files | Ignored |
| `knowledge/originals/` | Private input documents | Ignored |
| `knowledge/markdown/` | Canonical editable documents | Project choice |
| `knowledge/manifests/` | Provenance and checksums | Project choice |
| `output/` | Derived exports and renders | Ignored |
| `benchmarks/` | Latest acceptance evidence | Tracked |

## Trust boundaries and limitations

- `sandbox-exec` is deprecated and must be behaviorally revalidated on each
  supported macOS release. See [SANDBOX.md](SANDBOX.md).
- Local models can produce unsafe or incorrect commands; permission prompts and
  review remain required.
- SearXNG and the gateway intentionally cross the network only when manually
  started.
- Loopback services are unauthenticated and must never bind to other interfaces.
- The workbench does not protect against a compromised operating system or a
  malicious process already running as the same user.
