#!/usr/bin/env python3
"""Behaviorally verify that the platform sandbox allows loopback and denies external IPs."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import pathlib
import platform
import socketserver
import subprocess
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/sandbox/run.sh"
PROFILES = ("opencode", "llama", "documents")


class QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def resolve_profile(raw: str) -> str:
    path = pathlib.Path(raw)
    if path.suffix == ".sb":
        name = path.stem
        if name not in PROFILES:
            raise SystemExit(f"unknown Seatbelt profile stem: {name}")
        return name
    if raw in PROFILES:
        return raw
    raise SystemExit(f"unknown sandbox profile: {raw}")


def curl(profile: str, url: str) -> subprocess.CompletedProcess[str]:
    if not RUNNER.is_file():
        raise SystemExit(f"missing sandbox runner: {RUNNER}")
    curl_bin = "/usr/bin/curl" if pathlib.Path("/usr/bin/curl").is_file() else "curl"
    return subprocess.run(
        [str(RUNNER), "--profile", profile, "--", curl_bin, "--silent", "--show-error", "--max-time", "2", url],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def ensure_linux_prereqs() -> None:
    if platform.system() != "Linux":
        return
    if subprocess.run(["systemd-run", "--version"], capture_output=True, check=False).returncode != 0:
        raise SystemExit("Linux sandbox requires systemd-run (systemd user session ≥245)")
    # Fail early if user systemd is unavailable.
    probe = subprocess.run(
        ["systemd-run", "--user", "--collect", "--quiet", "--", "/bin/true"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise SystemExit(
            "Linux sandbox requires a working systemd --user session "
            f"(systemd-run --user failed: {probe.stderr.strip() or probe.stdout.strip()})"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        required=True,
        help="logical profile (opencode|llama|documents) or path to a macOS .sb file",
    )
    args = parser.parse_args()
    profile = resolve_profile(args.profile)
    ensure_linux_prereqs()

    if platform.system() == "Darwin":
        seatbelt = ROOT / "config/firewall" / f"{profile}.sb"
        if not seatbelt.is_file():
            raise SystemExit(f"missing sandbox profile: {seatbelt}")

    with socketserver.TCPServer(("127.0.0.1", 0), QuietHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            local = curl(profile, f"http://127.0.0.1:{server.server_address[1]}/")
        finally:
            server.shutdown()
            thread.join(timeout=2)

    if local.returncode != 0:
        detail = local.stderr.strip() or local.stdout.strip()
        raise SystemExit(f"sandbox blocked loopback unexpectedly: {detail}")

    external = curl(profile, "http://1.1.1.1/")
    if external.returncode == 0:
        raise SystemExit("sandbox unexpectedly allowed non-loopback networking")

    backend = "seatbelt" if platform.system() == "Darwin" else "systemd-run-ipfilter"
    print(f"sandbox probe passed ({backend}/{profile}): loopback allowed, non-loopback denied")
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)
