# Sandbox boundary and replacement path

## Current control

Normal OpenCode, llama.cpp, and document conversion processes run under
`sandbox-exec` profiles in `config/firewall/`. Each profile allows loopback and
denies non-loopback IP networking. `make check`, model/OpenCode preflight, and
`make test` run a behavioral probe that fails closed if loopback is blocked or
an external IP is allowed.

`sandbox-exec` is deprecated by Apple. Availability and observed behavior are
startup prerequisites, not a permanent guarantee.

## Operator expectations

1. Re-run `make check` after every macOS upgrade before trusting the workbench.
2. If the probe fails, stop using the workbench until a replacement boundary is
   reviewed and landed.
3. Keep application policy (OpenCode permissions, loopback binds, PID stop
   validation) even when the OS sandbox is healthy; it is defense in depth, not
   a substitute.

## Replacement options (reviewed later)

When Apple removes or weakens `sandbox-exec`, choose one explicit replacement
before continuing normal use:

| Option | Fit | Notes |
|---|---|---|
| Successor Seatbelt / App Sandbox tooling | Best continuity | Prefer if Apple documents a supported CLI equivalent |
| Process-scoped Packet Filter anchors | Strong network deny | Not process-aware by itself; pair with launch wrappers and audits |
| Network Extension / content filter | Strongest OS control | Conflicts with the no-always-on requirement unless manually started |
| Container / VM isolation | Strong filesystem+network | Out of current scope; would need a separate milestone |

No replacement is active today. Do not install always-on network extensions or
login items as a silent workaround.

## Proof commands

```sh
make check
make network-audit
python3 tools/sandbox-probe.py --profile config/firewall/opencode.sb
python3 tools/sandbox-probe.py --profile config/firewall/llama.sb
python3 tools/sandbox-probe.py --profile config/firewall/documents.sb
```
