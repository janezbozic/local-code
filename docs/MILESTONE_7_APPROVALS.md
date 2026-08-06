# Reviewed Linux installation commands (Milestone 7)

**Status:** code-complete; not yet a fully accepted publish path. macOS remains
the proven platform. Complete
[../benchmarks/LINUX_ACCEPTANCE.md](../benchmarks/LINUX_ACCEPTANCE.md) on a real
Linux host (fill `OPENCODE_BINARY_SHA256_LINUX_*` and record
`benchmarks/*-linux.json`) before advertising production Linux support.

These commands contact GitHub, npm, or Hugging Face and must be reviewed and
approved before use. They write only under this project except for system
packages you install with the distro package manager. Normal workbench
operation never runs them.

Pins remain in `config/versions.env`. Linux uses the same OpenCode npm package
and model SHA-256 pins as macOS; the native OpenCode binary SHA is
OS/architecture specific.

## Supported Linux shape

- x86_64 (primary) or aarch64
- systemd user session with `systemd-run --user` (typically systemd ≥ 245)
- Zsh on `PATH` (`#!/usr/bin/env zsh`)
- CUDA toolkit for the accepted GPU path, or explicit `LLAMA_GPU_BACKEND=cpu`

## 1. System packages (example: Debian/Ubuntu)

```sh
sudo apt-get update
sudo apt-get install -y zsh make git python3 python3-venv cmake ninja-build \
  jq shellcheck curl lsof ripgrep ca-certificates build-essential
```

Optional documents tooling:

```sh
sudo apt-get install -y libreoffice poppler-utils
```

NVIDIA CUDA toolkit/driver installation is distro-specific; install the vendor
packages before building llama.cpp with CUDA.

## 2. Install the pinned OpenCode V1 CLI locally

Same npm pin as macOS:

```sh
npm install --prefix .tools/opencode-v1 --save-exact opencode-ai@1.18.13
```

Record the native binary SHA after install:

```sh
sha256sum .tools/opencode-v1/node_modules/.bin/opencode
```

Write the digest into `config/versions.env` as
`OPENCODE_BINARY_SHA256_LINUX_X64` or `OPENCODE_BINARY_SHA256_LINUX_ARM64`.
Do not copy the darwin-arm64 digest.

## 3. Fetch and build pinned llama.cpp

```sh
git clone --depth 1 --branch b9637 https://github.com/ggml-org/llama.cpp.git .tools/llama.cpp
git -C .tools/llama.cpp rev-parse HEAD
```

CUDA build (accepted Linux GPU path):

```sh
cmake -S .tools/llama.cpp -B .tools/llama.cpp/build \
  -DGGML_CUDA=ON -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build .tools/llama.cpp/build --config Release --target llama-server llama-cli llama-bench -j "$(nproc)"
```

CPU-only smoke build (explicit bring-up only):

```sh
cmake -S .tools/llama.cpp -B .tools/llama.cpp/build \
  -DGGML_CUDA=OFF -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build .tools/llama.cpp/build --config Release --target llama-server -j "$(nproc)"
```

For CPU-only operation set in the environment or
`config/llama/runtime.linux.env`:

```sh
LLAMA_GPU_BACKEND=cpu
LLAMA_GPU_LAYERS=0
```

The reported llama.cpp commit must begin with `aedb2a5`; otherwise stop.

## 4. Models

Use the same model download commands and SHA-256 pins as
[MILESTONE_2_APPROVALS.md](MILESTONE_2_APPROVALS.md). Weights are portable;
context acceptance is not—record Linux evidence separately.

## 5. Linux acceptance evidence

With port 8080 free:

```sh
make check
make test
make network-audit
make benchmark-gpt-oss
```

Linux profile results write to `benchmarks/profiles-*-linux.json` and must not
overwrite macOS evidence files. Short-prompt gates do not prove a filled KV
cache; review RSS/swap after realistic sessions.

## 6. Sandbox backend

Linux isolation is `systemd-run --user` IP filtering via `tools/sandbox/run.sh`.
See [config/firewall/linux/README.md](../config/firewall/linux/README.md).
There is no Seatbelt `.sb` file on Linux.
