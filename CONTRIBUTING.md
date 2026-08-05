# Contributing

## Before contributing

Read `AGENTS.md`, `PLANS.md`, and `SECURITY.md`. Privacy and locality invariants
take precedence over convenience. Changes must not introduce hosted inference,
implicit downloads, automatic startup, telemetry, non-loopback bindings, or
parallel model requests.

The project does not yet declare an open-source license. External contributors
should wait for an explicit license and contribution policy before submitting
substantial code.

## Development workflow

1. Keep toolchains and runtime data in the existing ignored directories.
2. Make the smallest scoped change that satisfies the issue.
3. Update pins and approval records for any dependency or model change.
4. Update documentation whenever commands, ports, profiles, permissions, or
   trust boundaries change.
5. Run the required checks.

```sh
make check
make test
make network-audit
```

Run relevant optional tests and benchmarks when changing model, search, or
document behavior.

## Style

- Shell scripts use Zsh, `set -eu`, shared helpers from `tools/common.sh`, and
  explicit paths for sensitive operations.
- Python follows the standard library style already present in the repository;
  avoid adding dependencies when the standard library is sufficient.
- Configuration is exact-pinned and fail-closed.
- Documentation uses relative links and commands that run from the repository
  root.

## Pull requests

Describe:

- the problem and security impact;
- files and boundaries changed;
- commands run and their results;
- new downloads, dependencies, listeners, or persistent state;
- rollback steps.

Never attach private documents, runtime logs containing sensitive prompts, model
files, credentials, or internal paths.
