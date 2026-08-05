# Execution Plan

Last updated: 2026-08-05

## Invariants

1. LLM inference is local and uses only a server bound to `127.0.0.1`.
2. OpenCode, llama.cpp, and document tools cannot make non-loopback network connections during normal operation.
3. Dependencies, source, and models are downloaded only through explicit, reviewed commands.
4. Services have no automatic startup and are stopped manually.
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

## Milestone 1 decisions

- OpenCode V1 is selected and exact-pinned to npm package `opencode-ai@1.18.13`; upgrades remain manual. No custom VS Code extension is maintained by this repository.
- The only configured provider is `local-llama`, using `http://127.0.0.1:8080/v1`. The accepted default is IBM Granite 4.1 8B Q4_K_M with model ID `granite-4.1-8b`; it passed a native llama.cpp structured tool-call test. The larger gpt-oss-20b model remains available through its explicit profile. Qwen3.6 27B Q4_K_M is exact-pinned as a provisional 8K profile but remains unaccepted until it passes the memory, swap, thermal, generation, and tool-call gates on the 24 GB target.
- OpenCode state is isolated under `.runtime/opencode`; existing global credentials and plugins are not loaded.
- `sandbox-exec` enforces non-loopback denial. Its deprecated status is an explicit risk, mitigated by a mandatory behavioral probe.
- llama.cpp is built inside `.tools/llama.cpp` with Metal enabled. Models reside under gitignored `models/`.
- The 8192-token baseline failed the tool-reliability gate: repository glob/read output forced repeated compactions, and the second compaction produced no summary. The accepted Granite profile therefore uses 16384 context tokens, one parallel slot, and a 2048-token maximum response. OpenCode V1 compaction is automatic, prunes old tool output, and reserves 2048 tokens; memory, swap, and thermal observations are recorded in the benchmark evidence.
- OpenCode preview searches can re-include gitignored paths when the model supplies a positive glob and can accept model-selected result limits of 2000. A repository-owned ripgrep guard excludes toolchains, runtime state, models, originals, and outputs, and caps stdout at 250 rows so a single tool result cannot exceed the model context.
- No RAG, browser automation, database, container runtime, reverse proxy, telemetry stack, or worker queue is included.

## Implemented milestone details

### Milestone 2 — model lifecycle and benchmark

The exact OpenCode build, llama.cpp revision, and model artifacts are pinned in
`config/versions.env`. The active Granite Q4_K_M profile uses Metal, 16K context,
one slot, and a structured tool-call gate. Machine-readable acceptance evidence
is in `benchmarks/latest.json`; sequential 8K/16K cold-process comparisons and
clean unload proof are in `benchmarks/profiles.json`. Both profiles passed with
unchanged swap and no recorded thermal warning; 16K remains selected because it
prevents the tool-result compaction failures observed at 8K.

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
