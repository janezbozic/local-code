# Installation

## Supported environment

The repository currently supports:

- macOS on Apple Silicon;
- approximately 24 GB of unified memory for the recorded profiles;
- Zsh, Make, Git, Python 3, Node.js/npm, CMake, `jq`, `shellcheck`, `curl`,
  `lsof`, and standard macOS tools including `sandbox-exec` and `shasum`;
-   sufficient disk space for local builds, wheel caches, and models. The coding
  sufficient disk space for local builds, wheel caches, and models. The gpt-oss
  default is about 12.11 GB, Granite about 5.35 GB, Qwen2.5 Coder about 4.68 GB,
  and the provisional Qwen3.6 Q4_K_M file about 19.10 GB before runtime caches.

Other operating systems are not currently supported because the network
boundary and process checks are macOS-specific.

## Installation principles

Installation is deliberately manual. Review each command before running it.
Normal `make` targets do not install packages, update tools, or download models.
All installed toolchains, Python environments, models, and caches remain below
the repository except for system prerequisites you install separately.

Exact component pins are stored in `config/versions.env`.

## 1. Clone and inspect

```sh
git clone YOUR_REPOSITORY_URL local-code
cd local-code
sed -n '1,220p' AGENTS.md
sed -n '1,220p' config/versions.env
```

Before installing anything, verify that the repository is in a trusted location
and that ports 8080, 8888, and 8890 are not assigned to unrelated services.

## 2. Install system prerequisites

Use your preferred package manager to install the command-line prerequisites
listed above. On macOS, `/usr/bin/sandbox-exec`, `/usr/sbin/lsof`, and
`/usr/bin/shasum` are system tools. Do not replace the repository's pinned
OpenCode or `llama.cpp` binaries with global versions.

Confirm the key commands:

```sh
for command in git make python3 node npm cmake jq shellcheck curl; do
  command -v "$command" || exit 1
done
```

## 3. Install OpenCode V1

Run the exact project-local npm command and verify the binary:

```sh
npm install --prefix .tools/opencode-v1 --save-exact opencode-ai@1.18.13
tools/opencode/preflight.sh
```

The expected npm integrity, shasum, native-binary SHA-256, and postinstall notes
are recorded in [MILESTONE_2_APPROVALS.md](MILESTONE_2_APPROVALS.md).

## 4. Build `llama.cpp`

Clone the pinned tag, verify its commit, and build the Metal server using the
commands in [MILESTONE_2_APPROVALS.md](MILESTONE_2_APPROVALS.md). The expected
tag is `b9637`, and the commit must begin with `aedb2a5`.

The resulting executable must be:

```text
.tools/llama.cpp/build/bin/llama-server
```

The model preflight also verifies that CMake recorded `GGML_METAL=ON`.

## 5. Install a model

Granite is the default and should be installed first:

```text
models/granite-4.1-8b-Q4_K_M.gguf
```

Download it only from the immutable revision documented in
[MILESTONE_2_APPROVALS.md](MILESTONE_2_APPROVALS.md), then verify its exact byte
size and SHA-256. The optional gpt-oss model follows the same process and lives
at `models/gpt-oss-20b-mxfp4.gguf`.

Qwen3.6 27B is an optional provisional profile at
`models/Qwen3.6-27B-Q4_K_M.gguf`. On a 24 GB Mac, its 19.1 GB weights leave
little headroom for the operating system, KV cache, and runtime allocations.
Install it only if you accept that it may fail the memory/swap gate.

Do not rename an unverified file into an expected model path.

## 6. Optional restricted search

Search requires a project-local SearXNG checkout at the exact revision in
`config/versions.env` and a Python environment at `.venv/search`. Review
[MILESTONE_3_APPROVALS.md](MILESTONE_3_APPROVALS.md) before cloning sources or
resolving wheels. The safe MCP gateway itself uses only Python's standard
library.

Search is optional; the core workbench runs without it.

## 7. Optional document environment

Document conversion requires `.venv/documents`. Direct dependency pins are in
`config/documents/requirements.in`, with reviewed wheel hashes in
`config/versions.env`. Resolve and cache wheels explicitly under
`.tools/wheels/documents`, then install from that local cache. Never let a normal
document command contact a package index.

Document support is optional. Tests skip its integration suite when the
environment is absent.

## 8. Validate the installation

```sh
make check
make test
make network-audit
```

Then perform the first local run:

```sh
# Terminal 1
make model-start

# Terminal 2
make agent
```

If startup fails, do not bypass preflight checks. Use
[TROUBLESHOOTING.md](TROUBLESHOOTING.md) to identify the failed invariant.

## Upgrades

There is no automatic upgrade path. For every component upgrade:

1. record the new immutable version, revision, integrity, and hashes;
2. review configuration/schema changes;
3. rebuild in project-local paths;
4. rerun `make check`, `make test`, `make network-audit`, and relevant
   benchmarks;
5. update the approval and operations documentation in the same change.
