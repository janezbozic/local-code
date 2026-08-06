# Manual operations

All workbench components are manually started. There are no login items, launch
agents, scheduled jobs, or automatic updates. Run commands from the repository
root.

## Validation

Run `make check`, `make test`, and `make network-audit`. These commands do not
need the model or OpenCode runtime. The sandbox test briefly starts an ephemeral
loopback-only HTTP server and always shuts it down. Document integration tests
are skipped when the optional environment is absent.

## Model server

`make up` is the supervised single-user path: it starts the accepted gpt-oss
model in the background if needed, waits for health, optionally starts restricted
search when `SEARCH=1`, and then runs OpenCode in the foreground. `make down`
stops recorded search and model services. Neither command installs login items
or automatic restart.

`make model-start` remains available for an explicit server-only session. It
checks the pinned project-local binary, Metal-enabled CMake cache, model
existence and checksum, fixed localhost settings, sandbox behavior, and port
ownership before execution.

```sh
make up
# or
make model-start
```

gpt-oss is the accepted default at 128K context. Select other profiles explicitly:

```sh
make up PROFILE=granite
make model-start PROFILE=coder
make model-start PROFILE=qwen36
make agent PROFILE=qwen36
```

Do not treat `coder` or Qwen3.6 as accepted until their profile benchmarks pass
structured tool calling without new swap use or thermal warnings. Qwen3.6 Q4_K_M
weights alone are about 19.1 GB.

The agent profile must match the currently running server. Never start both
models concurrently. The model server listens only on `127.0.0.1:8080`.

Stop a foreground server with `Ctrl-C`. Optional `make model-start BACKGROUND=1` records PID, process start time, executable, command, working directory, host, and port in `.runtime/pids/model.json`. `make model-stop` validates that identity before signalling it.

## Agent

Start the TUI only after the model server passes its health check:

```sh
make agent
```

The wrapper uses `.runtime/opencode` for all XDG state and passes a minimal environment into the sandbox. It does not inherit API keys or global OpenCode configuration.

Useful direct probes:

```sh
tools/opencode/preflight.sh
tools/opencode/bin/opencode --version
```

The repository wrapper supports CLI subcommands such as `run` and `serve`, but
the normal interactive entry point remains `make agent`.

## Restricted web research

Run `make search-start` explicitly. It starts pinned SearXNG on
`127.0.0.1:8888` and the safe MCP gateway on `127.0.0.1:8890`, recording both
identities. `make search-stop` validates PID, start time, and command before
signalling either process. OpenCode reaches only the gateway through loopback.

Search services run in the background by design. Inspect their logs in
`.runtime/logs/searxng.log` and `.runtime/logs/web-gateway.log`.

## Documents

Document commands run in the repository no-external-network profile and use
the project-local pinned Python environment. See `docs/DOCUMENTS.md`. They
never install or fetch converters implicitly.

## Incident shutdown

1. Exit OpenCode normally.
2. Run `make down`, or `make model-stop` / `make search-stop` for the recorded services you started.
3. Run `make network-audit` and investigate any unexpected workbench listener or PID record.

Do not manually delete PID records until process identity and ownership have
been investigated. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
