#!/usr/bin/env python3
"""Behaviorally verify that a sandbox profile allows loopback and denies external IPs."""

from __future__ import annotations

import argparse
import contextlib
import http.server
import pathlib
import socketserver
import subprocess
import threading


class QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def curl(profile: pathlib.Path, url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-f",
            str(profile),
            "/usr/bin/curl",
            "--silent",
            "--show-error",
            "--max-time",
            "2",
            url,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=pathlib.Path)
    args = parser.parse_args()
    profile = args.profile.resolve()
    if not profile.is_file():
        raise SystemExit(f"missing sandbox profile: {profile}")

    with socketserver.TCPServer(("127.0.0.1", 0), QuietHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            local = curl(profile, f"http://127.0.0.1:{server.server_address[1]}/")
        finally:
            server.shutdown()
            thread.join(timeout=2)

    if local.returncode != 0:
        raise SystemExit(f"sandbox blocked loopback unexpectedly: {local.stderr.strip()}")

    external = curl(profile, "http://1.1.1.1/")
    if external.returncode == 0:
        raise SystemExit("sandbox unexpectedly allowed non-loopback networking")

    print("sandbox probe passed: loopback allowed, non-loopback denied")
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)

