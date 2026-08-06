# Execution Plan

Last updated: 2026-08-06

## Invariants

1. LLM inference is local and uses only a server bound to `127.0.0.1`.
2. OpenCode, llama.cpp, and document tools cannot make non-loopback network connections during normal operation.
3. Dependencies, source, and models are downloaded only through explicit, reviewed commands.
4. Services have no automatic startup and are stopped manually through supervised targets such as `make up` / `make down`.
5. Only one inference slot is permitted until memory measurements prove otherwise.
6. Web results are untrusted; later web access is mediated by the restricted local gateway.
7. Canonical new documents are Markdown. Originals and derived outputs never overwrite one another.

## Milestone status

| Milestone | Status | Exit condition |
|---|---|---|
| 1. Strict-local foundation | Implemented | `make check`, `make test`, and `make network-audit` pass without optional runtimes installed. |
| 2. Local model and benchmark | Implemented | Granite 4.1 8B, structured tool calling, 16K context, repository checks, memory/swap and thermal probes are recorded in `benchmarks/latest.json`. |
| 3. Restricted web research | Implemented | Pinned native SearXNG and the safe gateway provide DLP, SSRF/redirect revalidation, bounded extraction, citations, injection labels, and validated shutdown. |
| 4. Bounded agents | Implemented | Six roles have fail-closed permissions, one-level delegation, and one serialized llama slot. |
| 5. Document workflows | Implemented | Pinned Docling/document libraries and representative PDF/DOCX/PPTX/XLSX import plus export/render verification are present. |
| 6. Boundary proof | Implemented | Listener, PID ownership, model outbound sockets, sandbox behavior, normal shutdown, and stale-record checks are repeatable through `make network-audit` and lifecycle tests. |
| 7. Linux platform support | Code-complete; host acceptance pending | Platform sandbox façade, Linux systemd-run IP filter backend, CUDA/CPU llama preflight, portable paths/telemetry, and Linux approval docs are present. Full Linux acceptance requires filled `OPENCODE_BINARY_SHA256_LINUX_*` pins and `benchmarks/*-linux.json` from a real Linux host ([benchmarks/LINUX_ACCEPTANCE.md](benchmarks/LINUX_ACCEPTANCE.md)). |

## Milestone 1 decisions

- OpenCode V1 is selected and exact-pinned to npm package `opencode-ai@1.18.13`; upgrades remain manual. No custom VS Code extension is maintained by this repository.
- The only configured provider is `local-llama`, using `http://127.0.0.1:8080/v1`. The accepted default is gpt-oss-20b MXFP4 with model ID `gpt-oss-20b` at 128K context. IBM Granite 4.1 8B remains a selectable accepted profile at 16K. Qwen2.5 Coder 7B and Qwen3.6 27B are pinned provisional profiles and remain unaccepted until they pass structured tool-call, memory, swap, and thermal gates on the target machine.
- OpenCode state is isolated under `.runtime/opencode`; existing global credentials and plugins are not loaded.
- Network denial is enforced by a platform sandbox façade (`tools/sandbox/run.sh`): Seatbelt on macOS, `systemd-run --user` IP filters on Linux. Behavioral probes fail closed on both.
- llama.cpp is built inside `.tools/llama.cpp` with Metal on macOS and CUDA (or explicit CPU) on Linux. Models reside under gitignored `models/`.
- The 8192-token baseline failed the tool-reliability gate: repository glob/read output forced repeated compactions, and the second compaction produced no summary. Accepted profiles therefore use profile-specific contexts, one parallel slot, and a 2048-token maximum response. OpenCode V1 compaction is automatic, prunes old tool output, and reserves 2048 tokens.
- `make up` / `make down` provide supervised session lifecycle without login items, launch agents, systemd services, or automatic restart.
- OpenCode preview searches can re-include gitignored paths when the model supplies a positive glob and can accept model-selected result limits of 2000. A repository-owned ripgrep guard excludes toolchains, runtime state, models, originals, and outputs, and caps stdout at 250 rows so a single tool result cannot exceed the model context.
- No RAG, browser automation, database, container runtime, reverse proxy, telemetry stack, or worker queue is included. Linux isolation uses process-scoped systemd-run IP filtering, not containers.

## Implemented milestone details

### Milestone 2 — model lifecycle and benchmark

The exact OpenCode build, llama.cpp revision, and model artifacts are pinned in
`config/versions.env`. The accepted gpt-oss MXFP4 default uses Metal, 128K
context, one slot, and a structured tool-call gate; evidence is in
`benchmarks/profiles-gpt-oss.json`. Granite remains a selectable 16K profile.
The `coder` profile is pinned but currently fails the structured tool-call
gate, so it must not become the default.

### Milestone 3 — restricted web

Pinned, project-local SearXNG and the separately started gateway implement
`web_search`, `web_fetch`, `web_open`, and `web_find` with query DLP, DNS and
redirect revalidation, SSRF denial, content/time/size limits, readable
extraction, source metadata, stable references, and prompt-injection warnings.

### Milestone 4 — agents

Coordinator, researcher, explorer, implementer, reviewer, and document specialist
definitions have minimum tool permissions, serialized inference, one-level
delegation, Git worktree guidance, and fail-closed static policy tests.

### Milestone 5 — documents

The preserving lifecycle is `original → extraction → canonical Markdown →
export → render → inspection`. Docling and format libraries are exact-pinned;
conversion manifests include hashes, media type, converter, timestamp, outputs,
and page/sheet/slide counts. Representative format fixtures are tested.

### Milestone 6 — proof

The audit covers fixed ports, listener owners, model external sockets, PID
records, forbidden runtime configuration, and every sandbox profile. OpenCode,
llama.cpp, and document conversion deny non-loopback networking; only explicitly
started SearXNG and the fetch gateway cross the external boundary.

### Milestone 7 — Linux

`tools/sandbox/run.sh` selects Seatbelt on macOS or systemd-run IP filters on
Linux. Model preflight accepts Metal on macOS and CUDA (or explicit CPU) on
Linux. Document tools resolve LibreOffice and PDF preview helpers from PATH.
OpenCode binary pins are OS/arch specific. Linux acceptance evidence is written
to `benchmarks/*-linux.json` without overwriting macOS records. Reviewed Linux
install commands live in `docs/MILESTONE_7_APPROVALS.md`.
