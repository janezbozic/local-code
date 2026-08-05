# Troubleshooting

Do not bypass a failed preflight. Each failure represents an explicit security,
integrity, or lifecycle invariant.

## Start with diagnostics

```sh
make check
make test
make network-audit
```

Relevant logs and PID records are under `.runtime/logs` and `.runtime/pids`.
Runtime data is intentionally ignored by Git.

## OpenCode binary or checksum mismatch

Symptoms include `OpenCode V1 is not installed`, a version mismatch, or a
binary SHA-256 mismatch.

```sh
.tools/opencode-v1/node_modules/.bin/opencode --version
shasum -a 256 .tools/opencode-v1/node_modules/.bin/opencode
tools/opencode/preflight.sh
```

Expected version and hash are in `config/versions.env`. Reinstall only with the
exact reviewed command in `MILESTONE_2_APPROVALS.md`; never update in place.

## Model server will not start

Common causes are a missing model, checksum mismatch, non-Metal build, occupied
port 8080, or weakened sandbox behavior.

```sh
tools/model/preflight.sh
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

If a different process owns port 8080, identify it before stopping anything.
Do not change the configured port without updating and reviewing every boundary.

## OpenCode cannot reach the model

Confirm that the model server is still running and healthy:

```sh
curl --fail http://127.0.0.1:8080/health
```

The agent and server profiles must match. For gpt-oss, use `PROFILE=gpt-oss` on
both `model-start` and `agent`. A model ID selection does not load a different
GGUF file into an already-running server.

## `--port cannot be used with --mini`

Use `tools/opencode/bin/opencode` or `make agent`, not a stale copy of an older
wrapper. The current wrapper automatically disables the minimal interface when
`--port` is supplied.

## Stale model PID record

`make model-stop` refuses to remove a record when its PID is no longer running
or no longer matches the recorded process. This protects against PID reuse.

Inspect `.runtime/pids/model.json`, confirm with `ps` and `lsof` that the exact
recorded process is absent, and only then remove the stale JSON file manually.

## Restricted search does not start

Check that `.venv/search/bin/python` and `.venv/search/bin/searxng-run` exist,
then inspect:

```text
.runtime/logs/searxng.log
.runtime/logs/web-gateway.log
```

Ports 8888 and 8890 must be free. The gateway refusing a URL or query is usually
a policy decision, not a transport failure.

## Search shutdown refuses a PID

The stop script validates command markers and process start times. If validation
fails, inspect `.runtime/pids/search.json` and the live processes. Never signal a
PID merely because it appears in a stale record.

## Document tests are skipped

The document integration suite is optional and runs only when
`.venv/documents/bin/python` exists. Review the pinned dependencies and install
them into that project-local environment; do not install them globally.

## Document operation refuses to overwrite

This is expected. Originals, canonical Markdown, manifests, exports, and renders
are preserving artifacts. Choose a new output name or archive the existing file
after review; do not weaken overwrite protection.

## VS Code OpenCode sidebar says no data provider

The Marketplace beta `sst-dev.opencode-v2@0.1.1` declares a view without
registering its provider. This repository does not ship a custom replacement.
Use the terminal workflow or the official terminal-launching extension, with
the limitations documented in `VSCODE.md`.

## Network audit reports an unexpected listener

Treat this as an incident:

1. do not kill the PID until you identify its executable, command, parent, and
   working directory;
2. stop known workbench services through their normal stop commands;
3. rerun `make network-audit`;
4. preserve logs and PID records until the owner is understood.
