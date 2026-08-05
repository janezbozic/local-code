# Model benchmark records

Tracked benchmark JSON is acceptance evidence for one machine and point in
time, not a universal performance guarantee. Host-specific repository paths are
redacted as `<repo>` before publication.

`make benchmark` writes `latest.json`. A model profile is accepted only when the record reports successful local generation, structured tool calling, repository checks, the configured context size, and a single localhost listener. Memory pressure, swap, and thermal observations remain explicit review items.

`make benchmark-profiles` requires port 8080 to be free and writes
`profiles.json`. It cold-loads 8K and 16K sequentially, verifies generation and
structured tool calling, records RSS/swap/thermal state, and proves each server
is unloaded before the next profile starts.

`make benchmark-gpt-oss` performs the same sequential gate for the larger model
and writes `profiles-gpt-oss.json`. A failed profile does not change the default
Granite selection.

`make benchmark-qwen36` is the required provisional gate for Qwen3.6 27B and
writes `profiles-qwen36.json`. On the 24 GB target, monitor memory pressure and
swap closely; the 19.1 GB model file leaves little runtime headroom.

Benchmark history belongs in ignored `benchmarks/history`. Review records for
private paths or prompt content before committing them.
