# Restricted web boundary

`start.sh` launches pinned SearXNG and the standard-library MCP gateway on fixed
loopback ports and records their PID identities. `stop.sh` validates PID, start
time, and command marker before signalling. `gateway.py` supplies `web_search`,
`web_fetch`, `web_open`, and `web_find` with DLP, SSRF/redirect revalidation,
time/byte/type bounds, extraction, citations, and prompt-injection warnings.
