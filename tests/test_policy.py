#!/usr/bin/env python3
"""Static policy tests for the strict-local Milestone 1 configuration."""

from __future__ import annotations

import json
import hashlib
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_env(path: pathlib.Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result


def main() -> int:
    config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    if config.get("$schema") != "./config/opencode-v1.schema.json":
        fail("runtime config must use the repository-local schema reference")
    if config.get("share") != "disabled" or config.get("autoupdate") is not False:
        fail("sharing and automatic updates must be disabled")
    if set(config.get("provider", {})) != {"local-llama"}:
        fail("hosted provider detected")
    local_provider = config["provider"]["local-llama"]
    if local_provider.get("npm") != "@ai-sdk/openai-compatible":
        fail("local provider must use the OpenAI-compatible adapter")
    base_url = local_provider["options"]["baseURL"]
    if base_url != "http://127.0.0.1:8080/v1":
        fail("provider endpoint is not the fixed loopback URL")
    if local_provider["options"].get("apiKey") != "local-no-auth":
        fail("local provider must use the fixed non-secret compatibility key")
    if config.get("plugin"):
        fail("runtime config must not load plugins")
    if config.get("model") != "local-llama/gpt-oss-20b":
        fail("gpt-oss-20b must be the active local model")
    model = local_provider["models"]["gpt-oss-20b"]
    if model.get("limit") != {"context": 131072, "output": 2048}:
        fail("gpt-oss default must use the accepted 128K/2K token profile")
    granite = local_provider["models"].get("granite-4.1-8b", {})
    if granite.get("limit") != {"context": 16384, "output": 2048}:
        fail("selectable Granite profile is missing or malformed")
    coder = local_provider["models"].get("qwen2.5-coder-7b", {})
    if coder.get("limit") != {"context": 16384, "output": 2048}:
        fail("selectable provisional coder profile is missing or malformed")
    qwen36 = local_provider["models"].get("qwen3.6-27b", {})
    if qwen36.get("limit") != {"context": 8192, "output": 2048}:
        fail("selectable provisional Qwen3.6-27B profile is missing or malformed")
    if config.get("compaction") != {
        "auto": True,
        "prune": True,
        "reserved": 2048,
    }:
        fail("compaction must use the explicit 16K-context trial profile")
    mcp = config.get("mcp", {})
    if set(mcp) != {"local-safe-web"} or mcp["local-safe-web"].get("url") != "http://127.0.0.1:8890/mcp":
        fail("only the localhost safe-web MCP server may be configured")
    expected_agents = {"coordinator", "researcher", "explorer", "implementer", "reviewer", "document-specialist"}
    if set(config.get("agent", {})) != expected_agents:
        fail("bounded agent inventory is incomplete")
    if config.get("default_agent") != "coordinator":
        fail("coordinator must be the default agent")
    agents = config["agent"]
    coordinator_prompt = agents["coordinator"].get("prompt", "")
    for phrase in ("worktree", "reviewer", "serialized inference"):
        if phrase not in coordinator_prompt:
            fail(f"coordinator coding reliability prompt is missing: {phrase}")
    implementer_prompt = agents["implementer"].get("prompt", "")
    for phrase in ("smallest correct change", "opencode.json"):
        if phrase not in implementer_prompt:
            fail(f"implementer coding reliability prompt is missing: {phrase}")
    if agents["coordinator"].get("permission", {}).get("task") != "allow":
        fail("only the coordinator must be able to delegate")
    for name in expected_agents - {"coordinator"}:
        if agents[name].get("permission", {}).get("task") == "allow":
            fail(f"subagent {name} must not be able to delegate")
    researcher_rules = agents["researcher"].get("permission", {})
    if researcher_rules != {"*": "deny", "local-safe-web*": "allow"}:
        fail("researcher must be restricted to the safe-web namespace")
    researcher_system = agents["researcher"].get("prompt", "")
    for phrase in ("retrieval time", "stable line references", "contradictory sources"):
        if phrase not in researcher_system:
            fail(f"researcher evidence policy is missing: {phrase}")
    document_writes = agents["document-specialist"].get("permission", {}).get("edit", {})
    if document_writes != {
        "*": "deny",
        "knowledge/markdown/**": "allow",
        "knowledge/manifests/**": "allow",
        "output/**": "allow",
    }:
        fail("document specialist write scope is too broad or incomplete")
    implementer_writes = agents["implementer"].get("permission", {}).get("edit", {})
    if implementer_writes.get("*") != "allow":
        fail("implementer must allow ordinary repository edits")
    for path in (
        "opencode.json",
        "AGENTS.md",
        "config/firewall/**",
        "config/versions.env",
        "tools/web/**",
        "knowledge/originals/**",
    ):
        if implementer_writes.get(path) != "deny":
            fail(f"implementer must deny edits to security boundary path: {path}")

    permissions = config["permission"]
    for expected in {"external_directory", "webfetch", "websearch"}:
        if permissions.get(expected) != "deny":
            fail(f"missing deny rule: {expected}")

    runtime = parse_env(ROOT / "config/llama/runtime.env")
    if runtime.get("LLAMA_HOST") != "127.0.0.1":
        fail("llama.cpp host must be loopback")
    if runtime.get("LLAMA_CONTEXT") != "16384":
        fail("llama.cpp must use the 16K context trial profile")
    if runtime.get("LLAMA_PARALLEL") != "1":
        fail("only one inference slot is permitted")

    web_runtime = parse_env(ROOT / "config/web/runtime.env")
    if web_runtime.get("SEARXNG_HOST") != "127.0.0.1":
        fail("SearXNG host must be loopback")
    if web_runtime.get("WEB_GATEWAY_HOST") != "127.0.0.1":
        fail("web gateway host must be loopback")
    search_start = (ROOT / "tools/web/start.sh").read_text(encoding="utf-8")
    for required in ('assert_loopback "${SEARXNG_HOST}"', 'assert_loopback "${WEB_GATEWAY_HOST}"'):
        if required not in search_start:
            fail(f"search start must enforce loopback: {required}")
    check_script = (ROOT / "tools/check.sh").read_text(encoding="utf-8")
    if "tools/web/*.sh" not in check_script:
        fail("make check must shellcheck tools/web scripts")
    if "tools/workbench/*.sh" not in check_script:
        fail("make check must shellcheck tools/workbench scripts")
    if "tools/sandbox/*.sh" not in check_script:
        fail("make check must shellcheck tools/sandbox scripts")
    if "sandbox-probe.py --profile" not in check_script:
        fail("make check must behaviorally probe every sandbox profile")
    if "tools/sandbox/run.sh" not in (ROOT / "tools/model/start.sh").read_text(encoding="utf-8"):
        fail("model start must use the sandbox runner façade")
    if "tools/sandbox/run.sh" not in (ROOT / "tools/opencode/agent.sh").read_text(encoding="utf-8"):
        fail("OpenCode agent must use the sandbox runner façade")
    if not (ROOT / "docs/MILESTONE_7_APPROVALS.md").is_file():
        fail("Linux Milestone 7 approval document is missing")
    if not (ROOT / "docs/MILESTONE_8_APPROVALS.md").is_file():
        fail("WSL2 Milestone 8 approval document is missing")
    if not (ROOT / "benchmarks/WSL2_ACCEPTANCE.md").is_file():
        fail("WSL2 acceptance checklist is missing")
    if not (ROOT / "config/firewall/linux/README.md").is_file():
        fail("Linux firewall backend documentation is missing")
    common = (ROOT / "tools/common.sh").read_text(encoding="utf-8")
    for helper in ("is_wsl()", "require_linux_user_systemd()", "warn_wsl_repo_path()"):
        if helper not in common:
            fail(f"common.sh must define {helper} for WSL2/Linux sandbox gates")
    if "require_linux_user_systemd" not in (ROOT / "tools/sandbox/run.sh").read_text(encoding="utf-8"):
        fail("sandbox runner must require a working systemd --user session on Linux")
    if "is_wsl" not in (ROOT / "tools/sandbox-probe.py").read_text(encoding="utf-8"):
        fail("sandbox probe must detect WSL for clearer systemd failures")

    versions = parse_env(ROOT / "config/versions.env")
    if versions.get("OPENCODE_CHANNEL") != "stable":
        fail("OpenCode V1 must use the pinned stable channel")
    if versions.get("OPENCODE_PACKAGE") != "opencode-ai":
        fail("OpenCode V1 package pin is malformed")
    opencode_version = versions.get("OPENCODE_VERSION", "")
    if opencode_version != "1.18.13":
        fail("OpenCode V1 npm version pin is malformed")
    approvals = (ROOT / "docs/MILESTONE_2_APPROVALS.md").read_text(encoding="utf-8")
    if f"opencode-ai@{opencode_version}" not in approvals:
        fail("OpenCode version manifest and approval command are out of sync")
    if versions.get("OPENCODE_NPM_INTEGRITY", "") not in approvals:
        fail("OpenCode npm integrity pin is missing from approval instructions")
    document_requirements = (ROOT / "config/documents/requirements.in").read_text()
    for key, package in {
        "DOCLING_VERSION": "docling",
        "PYPDF_VERSION": "pypdf",
        "PDFPLUMBER_VERSION": "pdfplumber",
        "PYTHON_DOCX_VERSION": "python-docx",
        "OPENPYXL_VERSION": "openpyxl",
        "PYTHON_PPTX_VERSION": "python-pptx",
    }.items():
        if f"{package}=={versions.get(key, '')}" not in document_requirements:
            fail(f"document dependency pin is out of sync: {package}")
        wheel_hash = versions.get(key.replace("_VERSION", "_WHEEL_SHA256"), "")
        if not re.fullmatch(r"[0-9a-f]{64}", wheel_hash):
            fail(f"document wheel checksum pin is missing: {package}")

    installed_binary = ROOT / ".tools/opencode-v1/node_modules/.bin/opencode"
    if installed_binary.exists():
        actual_binary_sha = hashlib.sha256(installed_binary.read_bytes()).hexdigest()
        expected = versions.get("OPENCODE_BINARY_SHA256_DARWIN_ARM64") or versions.get("OPENCODE_BINARY_SHA256")
        if actual_binary_sha != expected:
            fail("installed OpenCode binary SHA-256 does not match the darwin-arm64 pin")
    if not re.fullmatch(r"[0-9a-f]{64}", versions.get("OPENCODE_BINARY_SHA256_DARWIN_ARM64", "")):
        fail("darwin-arm64 OpenCode binary pin is missing")

    wrapper = (ROOT / "tools/opencode/agent.sh").read_text(encoding="utf-8")
    required_flags = {
        "OPENCODE_DISABLE_AUTOUPDATE=1",
        "OPENCODE_DISABLE_DEFAULT_PLUGINS=1",
        "OPENCODE_DISABLE_LSP_DOWNLOAD=1",
        "OPENCODE_DISABLE_MODELS_FETCH=1",
        "OPENCODE_DISABLE_CLAUDE_CODE=1",
        "OPENCODE_ENABLE_EXA=0",
        "OPENCODE_PURE=1",
        "/usr/bin/env -i",
        ".runtime/opencode/bin",
        "/bin/ln -sf",
        "LOCAL_RG_BIN=",
        "rg-capped.sh",
        "interface_flags=(--pure --mini)",
        'model_flags=(--model "local-llama/${model_id}")',
        '"${interface_flags[@]}" "${model_flags[@]}"',
        "--port|--port=*)",
    }
    missing = sorted(flag for flag in required_flags if flag not in wrapper)
    if missing:
        fail(f"strict wrapper is missing: {', '.join(missing)}")

    vscode_shim = ROOT / "tools/opencode/bin/opencode"
    if not vscode_shim.exists() or "../agent.sh" not in vscode_shim.read_text(encoding="utf-8"):
        fail("VS Code terminal shim is missing")
    vscode_settings = json.loads((ROOT / ".vscode/settings.json").read_text(encoding="utf-8"))
    for key in ("terminal.integrated.env.osx", "terminal.integrated.env.linux"):
        terminal_path = vscode_settings.get(key, {}).get("PATH", "")
        if not terminal_path.startswith("${workspaceFolder}/tools/opencode/bin:"):
            fail(f"VS Code terminals do not prefer the strict OpenCode shim ({key})")

    for profile, expected in {
        "coder": ("qwen2.5-coder-7b", versions.get("CODER_MODEL_SHA256")),
        "granite": ("granite-4.1-8b", versions.get("MODEL_SHA256")),
        "gpt-oss": ("gpt-oss-20b", versions.get("GPT_OSS_MODEL_SHA256")),
        "qwen36": ("qwen3.6-27b", versions.get("QWEN36_MODEL_SHA256")),
    }.items():
        values = parse_env(ROOT / f"config/llama/profiles/{profile}.env")
        if values.get("LLAMA_MODEL_ID") != expected[0] or values.get("LLAMA_MODEL_SHA256") != expected[1]:
            fail(f"model profile pin is out of sync: {profile}")
        if profile == "gpt-oss" and values.get("LLAMA_CONTEXT") != "131072":
            fail("gpt-oss default must use accepted 128K context")
        if profile == "granite" and values.get("LLAMA_CONTEXT") != "16384":
            fail("granite must remain on 16K until 32K evidence lands")
        if profile in {"qwen36", "coder"} and values.get("LLAMA_CONTEXT") not in {"8192", "16384"}:
            fail(f"provisional profile context is malformed: {profile}")

    rg_guard = (ROOT / "tools/opencode/rg-capped.sh").read_text(encoding="utf-8")
    for excluded in [".git", ".tools", ".runtime", "models", "knowledge/originals", "output"]:
        if f"!**/{excluded}/**" not in rg_guard:
            fail(f"bounded ripgrep guard does not exclude {excluded}")
    if "NR <= 250" not in rg_guard:
        fail("bounded ripgrep guard does not enforce its result-row ceiling")

    forbidden_urls = re.compile(r"https?://(api\.)?(openai|anthropic|exa)\.", re.I)
    for path in [ROOT / "opencode.json", ROOT / "config/llama/runtime.env"]:
        if forbidden_urls.search(path.read_text(encoding="utf-8")):
            fail(f"hosted provider URL found in runtime configuration: {path}")

    required_targets = {
        "check",
        "model-start",
        "model-stop",
        "up",
        "down",
        "search-start",
        "search-stop",
        "agent",
        "network-audit",
        "document-import",
        "document-export",
        "document-render",
        "test",
        "benchmark-coder",
    }
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    defined = set(re.findall(r"^([a-z][a-z0-9-]*):", makefile, re.M))
    if missing_targets := sorted(required_targets - defined):
        fail(f"missing Make targets: {', '.join(missing_targets)}")

    print("static strict-local policy checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
