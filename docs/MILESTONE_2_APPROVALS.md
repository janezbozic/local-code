# Reviewed core installation commands

These commands contact GitHub, npm, or Hugging Face and must be reviewed and
approved before use. They write only under this project except for the optional
Homebrew Node installation. Normal workbench operation never runs them.

Pins are recorded in `config/versions.env`. Before execution, re-check that the immutable upstream objects still match the recorded metadata; do not silently substitute a newer release.

## 1. Install Node if no suitable local Node is available

```sh
brew install node
```

This is the only proposed system-level installation. An alternative is a checksummed project-local Node archive if system installation is not approved.

## 2. Install the pinned OpenCode V1 CLI locally

```sh
npm install --prefix .tools/opencode-v1 --save-exact opencode-ai@1.18.13
```

The registry metadata must report npm integrity `sha512-HYmBizm5vyAqqYuKzhpleRdEKwh7TeFSeA4f/Edl0F8OSPnbLi3DaXNMtmtsL13e2/994M9JoIz11yrVNdoAfA==` and package shasum `ac6c88ed6158f4535ef9a24614a3a35e635169d8`. The package exposes `.tools/opencode-v1/node_modules/.bin/opencode`. On this Apple Silicon installation the selected native binary SHA-256 is `47f80022654bee02dabd0467f7559bcdc195cb19159897652f41fde10f530547`; startup verifies it against `config/versions.env`.

Recent npm versions may warn that the package's install script is not covered by `allowScripts`. Do not approve it automatically. First check whether `.tools/opencode-v1/node_modules/.bin/opencode` exists and passes `tools/opencode/preflight.sh`; if it does, no script approval is needed.

## 3. Fetch and build pinned llama.cpp with Metal

```sh
git clone --depth 1 --branch b9637 https://github.com/ggml-org/llama.cpp.git .tools/llama.cpp
git -C .tools/llama.cpp rev-parse HEAD
cmake -S .tools/llama.cpp -B .tools/llama.cpp/build -DGGML_METAL=ON -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build .tools/llama.cpp/build --config Release --target llama-server llama-cli llama-bench -j 8
```

The reported commit must begin with `aedb2a5`; otherwise stop.

## 4. Download the active pinned model (4.98 GiB)

```sh
curl --fail --location --output models/granite-4.1-8b-Q4_K_M.gguf https://huggingface.co/ibm-granite/granite-4.1-8b-GGUF/resolve/865b82c2e7970d82e3731278c88c57ae7138359c/granite-4.1-8b-Q4_K_M.gguf
shasum -a 256 models/granite-4.1-8b-Q4_K_M.gguf
```

The exact size must be 5,347,914,400 bytes and SHA-256 must be `ed902ac9eb6adce5a90c6a08c8ea201b50e23fdc5976d1cd0362006afac5309e`. The immutable Hugging Face revision is `865b82c2e7970d82e3731278c88c57ae7138359c`.

## 5. Optional gpt-oss-20b model

```sh
curl --fail --location --output models/gpt-oss-20b-mxfp4.gguf https://huggingface.co/ggml-org/gpt-oss-20b-GGUF/resolve/4fec29804e3af052b602946deec2d3e62a6015e0/gpt-oss-20b-mxfp4.gguf
shasum -a 256 models/gpt-oss-20b-mxfp4.gguf
```

The SHA-256 must be `be37a636aca0fc1aae0d32325f82f6b4d21495f06823b5fbc1898ae0303e9935` and the verified downloaded size is 12,109,566,560 bytes. Delete or quarantine a mismatched download; never start it.
