# VS Code notes

No OpenCode VS Code extension is installed or maintained by this repository.
The removed custom sidebar and its build artifacts are not part of the
workbench.

The Marketplace `sst-dev.opencode-v2@0.1.1` beta declares a sidebar view but
does not register a view provider, producing the "no data provider" message.
The official `sst-dev.opencode@0.0.13` extension launches a terminal rather than
providing a Codex-like docked chat.

OpenCode V1 remains available through the terminal. Start the matching model,
then launch the strict wrapper:

```sh
make up
# or
make model-start PROFILE=gpt-oss
MODEL_PROFILE=gpt-oss tools/opencode/bin/opencode
```
