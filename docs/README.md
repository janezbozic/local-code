# Documentation

## Getting started

- [Installation](INSTALLATION.md): platform requirements, pinned components,
  installation order, and first-run verification.
- [Manual operations](OPERATIONS.md): daily startup, shutdown, profiles,
  research services, documents, and incident shutdown.
- [Troubleshooting](TROUBLESHOOTING.md): common preflight, model, OpenCode,
  network, search, document, and VS Code failures.

## Design and trust

- [Architecture](ARCHITECTURE.md): components, data flow, ports, state, and
  trust boundaries.
- [Sandbox boundary](SANDBOX.md): behavioral probes and replacement path for
  deprecated `sandbox-exec`.
- [Network and process isolation](../config/firewall/README.md): threat model
  and enforcement layers.
- [Bounded agents](../agents/README.md): roles, permissions, and delegation.
- [Execution plan](../PLANS.md): implemented milestones and design decisions.
- [Security policy](../SECURITY.md): supported scope and vulnerability reports.

## Features

- [Restricted web boundary](../tools/web/README.md)
- [Document lifecycle](DOCUMENTS.md)
- [Model benchmark records](../benchmarks/README.md)
- [VS Code notes](VSCODE.md)

## Provenance and reviewed installation commands

- [Core runtime approvals](MILESTONE_2_APPROVALS.md)
- [Restricted-search approvals](MILESTONE_3_APPROVALS.md)

These approval records preserve exact versions, revisions, hashes, and commands.
They are intentionally separate from normal operation because the workbench
must never download or update software implicitly.
