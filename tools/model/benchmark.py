#!/usr/bin/env python3
"""Run the local model acceptance benchmark and write a reproducible JSON record."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import platform
import resource
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[2]
ENDPOINT = "http://127.0.0.1:8080"
RESULT = ROOT / "benchmarks" / "latest.json"


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def request(path: str, payload: dict | None = None, timeout: float = 180) -> tuple[dict, float]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read())
    return body, time.monotonic() - started


def process_snapshot(pid: int) -> dict:
    proc = command("ps", "-p", str(pid), "-o", "rss=,vsz=,%cpu=,etime=,command=")
    fields = proc.stdout.strip().split(None, 4)
    return {
        "rss_kib": int(fields[0]) if len(fields) > 0 else None,
        "vsz_kib": int(fields[1]) if len(fields) > 1 else None,
        "cpu_percent": float(fields[2]) if len(fields) > 2 else None,
        "elapsed": fields[3] if len(fields) > 3 else None,
        "command": fields[4] if len(fields) > 4 else None,
    }


def main() -> int:
    try:
        health, health_seconds = request("/health", timeout=5)
        models, _ = request("/v1/models", timeout=5)
    except (OSError, urllib.error.URLError) as exc:
        print(f"error: local model server is unavailable: {exc}", file=sys.stderr)
        return 2

    listener = command("lsof", "-nP", "-t", "-iTCP:8080", "-sTCP:LISTEN")
    pids = [int(item) for item in listener.stdout.split() if item.isdigit()]
    if len(pids) != 1:
        print("error: expected exactly one listener owner on port 8080", file=sys.stderr)
        return 2
    pid = pids[0]
    before = process_snapshot(pid)
    swap_before = command("sysctl", "-n", "vm.swapusage").stdout.strip()

    generation_payload = {
        "model": "granite-4.1-8b",
        "messages": [{"role": "user", "content": "Reply with exactly BENCHMARK_OK."}],
        "temperature": 0,
        "max_tokens": 32,
    }
    generation, generation_seconds = request("/v1/chat/completions", generation_payload)
    choice = generation.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "").strip()
    usage = generation.get("usage", {})
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)

    tool_payload = {
        "model": "granite-4.1-8b",
        "messages": [{"role": "user", "content": "Call run_checks now. Do not answer in prose."}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "run_checks",
                "description": "Run repository checks",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }],
        "tool_choice": "required",
        "temperature": 0,
        "max_tokens": 128,
    }
    tool_response, tool_seconds = request("/v1/chat/completions", tool_payload)
    tool_choice = tool_response.get("choices", [{}])[0]
    calls = tool_choice.get("message", {}).get("tool_calls", [])
    structured_tool = bool(calls and calls[0].get("function", {}).get("name") == "run_checks")

    checks_started = time.monotonic()
    checks = command("make", "check")
    tests = command("make", "test")
    checks_seconds = time.monotonic() - checks_started

    after = process_snapshot(pid)
    swap_after = command("sysctl", "-n", "vm.swapusage").stdout.strip()
    thermal = command("pmset", "-g", "therm").stdout.strip()
    memory_pressure = command("memory_pressure", "-Q").stdout.strip()
    props, _ = request("/props", timeout=5)

    passed = all([
        health.get("status") == "ok",
        content == "BENCHMARK_OK",
        structured_tool,
        checks.returncode == 0,
        tests.returncode == 0,
        props.get("default_generation_settings", {}).get("n_ctx") == 16384,
    ])
    result = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "passed": passed,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "server": {
            "endpoint": ENDPOINT,
            "health": health,
            "health_seconds": health_seconds,
            "pid": pid,
            "models": models,
            "context_tokens": props.get("default_generation_settings", {}).get("n_ctx"),
            "process_before": before,
            "process_after": after,
        },
        "generation": {
            "expected": "BENCHMARK_OK",
            "actual": content,
            "seconds": generation_seconds,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": completion_tokens,
            "tokens_per_second": completion_tokens / generation_seconds if generation_seconds else None,
        },
        "tool_call": {
            "passed": structured_tool,
            "seconds": tool_seconds,
            "finish_reason": tool_choice.get("finish_reason"),
            "calls": calls,
        },
        "repository_checks": {
            "seconds": checks_seconds,
            "check_exit": checks.returncode,
            "test_exit": tests.returncode,
            "check_output": (checks.stdout + checks.stderr)[-4000:],
            "test_output": (tests.stdout + tests.stderr)[-4000:],
        },
        "system": {
            "swap_before": swap_before,
            "swap_after": swap_after,
            "memory_pressure": memory_pressure,
            "thermal": thermal,
            "benchmark_max_rss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "benchmark_max_rss_unit": "bytes" if sys.platform == "darwin" else "KiB",
        },
        "limitations": [
            "Cold-load duration is taken from the separately timed model-start operation.",
            "macOS compressed-memory attribution is system-wide and must be reviewed in Activity Monitor.",
            "Thermal output is best-effort because powermetrics requires elevated privileges.",
        ],
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"benchmark {'passed' if passed else 'failed'}; result: {RESULT.relative_to(ROOT)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
