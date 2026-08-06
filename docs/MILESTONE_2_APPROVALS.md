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

## 6. Optional provisional Qwen3.6 27B model (17.8 GiB)

```sh
curl --fail --location --output models/Qwen3.6-27B-Q4_K_M.gguf https://huggingface.co/ggml-org/Qwen3.6-27B-GGUF/resolve/8a7ee08e8b9bfb857107ecc25a5599d2f38b76f8/Qwen3.6-27B-Q4_K_M.gguf
shasum -a 256 models/Qwen3.6-27B-Q4_K_M.gguf
```

The exact size must be 19,095,766,304 bytes and SHA-256 must be
`65b753ea835627f7b511143c6ceb976525c7f21f5df8c664bc0a9c23d1c49921`.
The immutable GGUF revision is
`8a7ee08e8b9bfb857107ecc25a5599d2f38b76f8`; its `.src_sha` records official
Qwen source revision `6a9e13bd6fc8f0983b9b99948120bc37f49c13e9`.

This profile is not accepted yet. The file consumes most of a 24 GB machine's
available memory before KV cache and operating-system use. After explicit
download approval, start at 8K context and run `make benchmark-qwen36` with port
8080 free. A failed memory, swap, thermal, generation, or tool-call gate must
leave the coding default unchanged.

## 7. Coding-default Qwen2.5 Coder 7B model

```sh
curl --fail --location --output models/qwen2.5-coder-7b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf
shasum -a 256 models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
```

The exact size must be 4,683,073,536 bytes and SHA-256 must be
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`.
Delete or quarantine a mismatched download; never start it. After install, run
`make benchmark-coder` with port 8080 free. Do not make this the default until
structured tool calling passes; current evidence in `benchmarks/profiles-coder.json`
shows generation succeeding while required tool calls fail.
