#!/usr/bin/env python3
"""Validate the public documentation set and publication hygiene."""

from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "PLANS.md",
    "docs/README.md",
    "docs/INSTALLATION.md",
    "docs/ARCHITECTURE.md",
    "docs/OPERATIONS.md",
    "docs/TROUBLESHOOTING.md",
    "docs/DOCUMENTS.md",
    "docs/VSCODE.md",
}
EXCLUDED_PARTS = {".git", ".tools", ".runtime", ".venv", "models", "output"}
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PRIVATE_MAC_PATH = re.compile(r"/Users/[^/\s]+/")


def main() -> int:
    missing = sorted(path for path in REQUIRED if not (ROOT / path).is_file())
    if missing:
        raise AssertionError(f"missing public documentation: {', '.join(missing)}")

    errors: list[str] = []
    for document in sorted(ROOT.rglob("*.md")):
        if EXCLUDED_PARTS.intersection(document.relative_to(ROOT).parts):
            continue
        text = document.read_text(encoding="utf-8")
        if PRIVATE_MAC_PATH.search(text):
            errors.append(f"{document.relative_to(ROOT)} contains an absolute macOS home path")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                errors.append(
                    f"{document.relative_to(ROOT)} has a missing link target: {target}"
                )
    if errors:
        raise AssertionError("\n".join(errors))

    print("documentation and publication hygiene checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
