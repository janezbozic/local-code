#!/usr/bin/env python3
"""Sequential cold-load acceptance benchmark for profile contexts."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import pathlib
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER = ROOT / ".tools/llama.cpp/build/bin/llama-server"
SANDBOX = ROOT / "tools/sandbox/run.sh"
MODELS = {
    "coder": (ROOT / "models/qwen2.5-coder-7b-instruct-q4_k_m.gguf", "qwen2.5-coder-7b", "profiles-coder"),
    "granite": (ROOT / "models/granite-4.1-8b-Q4_K_M.gguf", "granite-4.1-8b", "profiles"),
    "gpt-oss": (ROOT / "models/gpt-oss-20b-mxfp4.gguf", "gpt-oss-20b", "profiles-gpt-oss"),
    "qwen36": (ROOT / "models/Qwen3.6-27B-Q4_K_M.gguf", "qwen3.6-27b", "profiles-qwen36"),
}
DEFAULT_CONTEXTS = {
    "coder": (16384, 32768),
    "granite": (16384, 32768),
    "gpt-oss": (32768, 131072),
    "qwen36": (8192, 16384),
}


def request(path: str, payload: dict | None = None, timeout: float = 180) -> tuple[dict, float]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request("http://127.0.0.1:8080" + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST" if data is not None else "GET")
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read()), time.monotonic() - started


def shell(*args: str) -> str:
    return subprocess.run(args, text=True, capture_output=True, check=False).stdout.strip()


def result_path_for(stem: str) -> pathlib.Path:
    suffix = "-linux" if platform.system() == "Linux" else ""
    return ROOT / "benchmarks" / f"{stem}{suffix}.json"


def swap_snapshot() -> str:
    if platform.system() == "Darwin":
        return shell("sysctl", "-n", "vm.swapusage")
    meminfo = pathlib.Path("/proc/meminfo")
    if meminfo.is_file():
        values = {}
        for line in meminfo.read_text().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key] = value.strip()
        return f"SwapTotal={values.get('SwapTotal', '?')} SwapFree={values.get('SwapFree', '?')}"
    return "swap:unavailable"


def thermal_snapshot() -> str:
    if platform.system() == "Darwin":
        return shell("pmset", "-g", "therm") or "thermal:unavailable"
    zones = sorted(pathlib.Path("/sys/class/thermal").glob("thermal_zone*/temp"))
    if not zones:
        return "thermal:unavailable"
    readings = []
    for zone in zones[:4]:
        try:
            millideg = int(zone.read_text().strip())
            readings.append(f"{zone.parent.name}={millideg / 1000:.1f}C")
        except (OSError, ValueError):
            continue
    return " ".join(readings) if readings else "thermal:unavailable"


def thermal_ok(value: str) -> bool:
    lower = value.lower()
    if "unavailable" in lower:
        return True
    if platform.system() == "Darwin":
        return "no thermal warning" in lower
    return True


def snapshot(pid: int) -> dict:
    fields = shell("ps", "-p", str(pid), "-o", "rss=,%cpu=,etime=").split()
    rss = int(fields[0]) if fields else None
    if rss is not None and platform.system() == "Darwin":
        # macOS ps RSS is in KiB already for modern ps; keep as reported.
        pass
    return {"rss_kib": rss,
            "cpu_percent": float(fields[1]) if len(fields) > 1 else None,
            "elapsed": fields[2] if len(fields) > 2 else None}


def benchmark(context: int, model: pathlib.Path, model_id: str, profile_name: str) -> dict:
    log_path = ROOT / ".runtime/logs" / f"profile-{profile_name}-{context}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    gpu_layers = os.environ.get("LLAMA_GPU_LAYERS", "999")
    command = [str(SANDBOX), "--profile", "llama", "--", str(SERVER),
        "--model", str(model), "--host", "127.0.0.1", "--port", "8080",
        "--ctx-size", str(context), "--parallel", "1", "--n-gpu-layers", str(gpu_layers), "--jinja"]
    swap_before = swap_snapshot()
    started = time.monotonic()
    with log_path.open("w") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"server exited during cold load; inspect {log_path}")
            try:
                health, _ = request("/health", timeout=1)
                if health.get("status") == "ok": break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("server cold-load health timeout")
        cold_load = time.monotonic() - started
        generation_payload = {
            "model": model_id, "messages": [{"role": "user", "content": "Reply with exactly PROFILE_OK."}],
            "temperature": 0, "max_tokens": 128}
        if profile_name == "gpt-oss":
            generation_payload["reasoning_effort"] = "low"
        response, generation_seconds = request("/v1/chat/completions", generation_payload)
        message = response.get("choices", [{}])[0].get("message", {})
        usage = response.get("usage", {})
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        tool_payload = {
            "model": model_id, "messages": [{"role": "user", "content": "Call profile_check now. Do not answer in prose."}],
            "tools": [{"type": "function", "function": {"name": "profile_check", "description": "Validate this profile", "parameters": {"type": "object", "properties": {}, "required": []}}}],
            "tool_choice": "required", "temperature": 0, "max_tokens": 128}
        if profile_name == "gpt-oss":
            tool_payload["reasoning_effort"] = "low"
        tool_response, tool_seconds = request("/v1/chat/completions", tool_payload)
        calls = tool_response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
        props, _ = request("/props", timeout=5)
        thermal = thermal_snapshot()
        swap_after = swap_snapshot()
        result = {"context_tokens": context,
            "reported_context_tokens": props.get("default_generation_settings", {}).get("n_ctx"),
            "cold_load_seconds": cold_load,
            "generation": {"seconds": generation_seconds, "actual": message.get("content", "").strip(),
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": completion_tokens,
                "tokens_per_second": completion_tokens / generation_seconds if generation_seconds else None},
            "tool_call": {"seconds": tool_seconds, "passed": bool(calls and calls[0].get("function", {}).get("name") == "profile_check")},
            "process": snapshot(process.pid), "swap_before": swap_before,
            "swap_after": swap_after, "thermal": thermal,
            "host": platform.platform()}
        result["passed"] = all([result["reported_context_tokens"] == context,
            result["generation"]["actual"] == "PROFILE_OK", result["tool_call"]["passed"],
            result["swap_before"] == result["swap_after"], thermal_ok(thermal)])
        return result
    finally:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
        if shell("lsof", "-nP", "-t", "-iTCP:8080", "-sTCP:LISTEN"):
            raise RuntimeError(f"profile {context} left a listener behind")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(MODELS), default="gpt-oss")
    parser.add_argument("--contexts", default="", help="comma-separated context sizes; defaults depend on profile")
    args = parser.parse_args()
    model, model_id, stem = MODELS[args.profile]
    result_path = result_path_for(stem)
    if not SERVER.is_file() or not model.is_file():
        print("error: pinned server or model is missing", file=sys.stderr); return 2
    if not SANDBOX.is_file():
        print("error: sandbox runner is missing", file=sys.stderr); return 2
    if shell("lsof", "-nP", "-t", "-iTCP:8080", "-sTCP:LISTEN"):
        print("error: port 8080 must be free before the profile benchmark", file=sys.stderr); return 2
    if args.contexts.strip():
        contexts = [int(item.strip()) for item in args.contexts.split(",") if item.strip()]
    else:
        contexts = list(DEFAULT_CONTEXTS[args.profile])
    profiles = [benchmark(context, model, model_id, args.profile) for context in contexts]
    accepted = None
    for item in profiles:
        if item["passed"]:
            accepted = item["context_tokens"]
    record = {"schema_version": 1, "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sequential": True, "parallel_slots": 1, "profile": args.profile, "model": model.name,
        "host": platform.platform(), "profiles": profiles,
        "accepted_context_tokens": accepted,
        "passed": any(item["passed"] for item in profiles) and profiles[0]["passed"]}
    result_path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"profile benchmark {'passed' if record['passed'] else 'failed'}; accepted_context={accepted}; result: {result_path.relative_to(ROOT)}")
    return 0 if record["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
