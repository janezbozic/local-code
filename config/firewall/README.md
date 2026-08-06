# Network and Process Isolation Policy

## Threat model

Protected data includes prompts, code, private filenames and identifiers, documents, tool output, credentials, and conversation history. Relevant threats are accidental provider discovery, inherited API credentials, update/model/plugin downloads, session sharing, malicious web instructions, SSRF, unsafe redirects, and a local service bound beyond loopback.

OpenCode configuration is necessary but not sufficient. The runtime wrapper therefore combines:

1. project-local XDG configuration/data/state/cache directories;
2. a scrubbed environment containing no hosted-provider credentials;
3. OpenCode disable flags and the isolated V1 `--pure --mini` interface with an explicit local model argument;
4. a provider allowlist and explicit web/provider permission denials; and
5. an OS-level network jail denying non-loopback networking (`sandbox-exec` on
   macOS; `systemd-run --user` IP filters on Linux via `tools/sandbox/run.sh`).

On macOS, `sandbox-exec` is deprecated by Apple and remains a behavioral
prerequisite. On Linux, a working systemd user session is required. In both
cases `tools/sandbox-probe.py` verifies that loopback succeeds and an external
IP is denied for every logical profile during `make check`. Startup fails closed
if that probe fails. See [docs/SANDBOX.md](../../docs/SANDBOX.md) and
[linux/README.md](linux/README.md).

The profiles intentionally focus on networking. OpenCode tool permissions enforce interactive file/command approvals, while the repository location and designated document directories provide the operational filesystem boundary.

## Network flow

| Process | Destination | Normal-use policy | Enforcement |
|---|---|---|---|
| OpenCode | `127.0.0.1:8080` llama.cpp | Allow | provider allowlist + sandbox |
| OpenCode | `127.0.0.1:8890` safe MCP gateway | Allow when manually started | MCP permission + sandbox |
| OpenCode and child shell commands | Any non-loopback IP | Deny | sandbox |
| llama.cpp | Any outbound non-loopback IP | Deny | sandbox |
| llama.cpp | Inbound `127.0.0.1:8080` | Allow | fixed arguments + sandbox + audit |
| Document tools | Any non-loopback IP | Deny | sandbox |
| SearXNG | Configured search engines | Allow only while manually running | separate process + PID/listener audit |
| Safe fetch gateway | Validated selected HTTP(S) pages | Allow only while manually running | application SSRF policy + PID/listener audit |

The built-in macOS Application Firewall does not provide this outbound per-process guarantee. PF is not used as the primary control because it is not process-aware. No third-party always-running network extension is installed because that would conflict with the manual-start requirement.
