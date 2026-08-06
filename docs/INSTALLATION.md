# Installation

## Supported environment

**macOS on Apple Silicon is the supported, proven publish path.** Linux x86_64
is code-complete (Milestone 7) but not fully accepted until Linux binary pins
and `benchmarks/*-linux.json` evidence exist—see
[../benchmarks/LINUX_ACCEPTANCE.md](../benchmarks/LINUX_ACCEPTANCE.md).

The repository targets:

- macOS on Apple Silicon with Metal-enabled llama.cpp and Seatbelt isolation
  (supported);
- Linux x86_64 with a systemd user session, `systemd-run --user` IP filtering,
  and CUDA-enabled llama.cpp (CPU bring-up allowed explicitly; acceptance
  pending host evidence);
- approximately 24 GB of memory for the recorded macOS profiles (Linux VRAM/RAM
  needs depend on the selected model and context);
- Zsh (`#!/usr/bin/env zsh`), Make, Git, Python 3, Node.js/npm, CMake, `jq`,
  `shellcheck`, `curl`, `lsof`, and platform sandbox tooling
  (`sandbox-exec` on macOS; `systemd-run` on Linux);
- sufficient disk space for local builds, wheel caches, and models. The gpt-oss
  default is about 12.11 GB, Granite about 5.35 GB, Qwen2.5 Coder about 4.68 GB,
  and the provisional Qwen3.6 Q4_K_M file about 19.10 GB before runtime caches.

Windows is not supported. Do not claim production Linux support in releases
until the Linux acceptance checklist has been completed and committed.

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

Install the packages listed for your OS:

- macOS: follow the Homebrew/Xcode notes in historical setup docs; ensure
  `/usr/bin/sandbox-exec`, `lsof`, `zsh`, and Metal-capable tooling are present.
- Linux: see [MILESTONE_7_APPROVALS.md](MILESTONE_7_APPROVALS.md) for package and
  CUDA/CPU build commands.

## 3. Reviewed component installs

- Core macOS/runtime pins: [MILESTONE_2_APPROVALS.md](MILESTONE_2_APPROVALS.md)
- Restricted search: [MILESTONE_3_APPROVALS.md](MILESTONE_3_APPROVALS.md)
- Linux builds and binary pins: [MILESTONE_7_APPROVALS.md](MILESTONE_7_APPROVALS.md)

## 4. First-run verification

```sh
make check
make test
make network-audit
```

Then start a session with `make up` after the model is installed.
