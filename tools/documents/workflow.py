#!/usr/bin/env python3
"""Preserving document import, canonical Markdown, export, render, and manifests."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import mimetypes
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
ORIGINALS = ROOT / "knowledge/originals"
MARKDOWN = ROOT / "knowledge/markdown"
MANIFESTS = ROOT / "knowledge/manifests"
OUTPUT = ROOT / "output"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main", "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SOFFICE = pathlib.Path("/opt/homebrew/bin/soffice")


def office_command(*args: str) -> list[str]:
    if not SOFFICE.is_file():
        raise ValueError("LibreOffice is not installed at /opt/homebrew/bin/soffice")
    profile = ROOT / ".runtime/libreoffice"
    profile.mkdir(parents=True, exist_ok=True)
    return [str(SOFFICE), f"-env:UserInstallation={profile.resolve().as_uri()}", "--headless", *args]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_new(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"refusing to overwrite existing canonical/derived file: {path}")
    path.write_text(content, encoding="utf-8")


def office_text(path: pathlib.Path) -> tuple[str, int, str]:
    suffix = path.suffix.lower()
    with zipfile.ZipFile(path) as archive:
        if suffix == ".docx":
            root = ET.fromstring(archive.read("word/document.xml"))
            paragraphs = ["".join(node.itertext()).strip() for node in root.findall(".//w:p", NS)]
            return "\n\n".join(item for item in paragraphs if item), 1, "python-stdlib-ooxml"
        if suffix == ".pptx":
            slides = sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))
            chunks = []
            for index, name in enumerate(slides, 1):
                root = ET.fromstring(archive.read(name))
                text = "\n".join(node.text or "" for node in root.findall(".//a:t", NS))
                chunks.append(f"## Slide {index}\n\n{text}")
            return "\n\n".join(chunks), len(slides), "python-stdlib-ooxml"
        if suffix == ".xlsx":
            shared = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(node.itertext()) for node in shared_root.findall(".//s:si", NS)]
            sheets = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
            chunks = []
            for index, name in enumerate(sheets, 1):
                root = ET.fromstring(archive.read(name))
                rows = []
                for row in root.findall(".//s:row", NS):
                    values = []
                    for cell in row.findall("s:c", NS):
                        value = cell.find("s:v", NS)
                        text = "" if value is None else (shared[int(value.text)] if cell.get("t") == "s" and value.text else value.text or "")
                        values.append(text.replace("|", "\\|"))
                    rows.append("| " + " | ".join(values) + " |")
                chunks.append(f"## Sheet {index}\n\n" + "\n".join(rows))
            return "\n\n".join(chunks), len(sheets), "python-stdlib-ooxml"
    raise ValueError(f"unsupported office format: {suffix}")


def extract(path: pathlib.Path) -> tuple[str, int | None, str]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".tsv"}:
        return path.read_text(encoding="utf-8", errors="replace"), None, "python-stdlib-text"
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return office_text(path)
    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore
        except ImportError as exc:
            raise ValueError("PDF import requires the pinned document Python environment") from exc
        reader = pypdf.PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages), f"pypdf-{pypdf.__version__}"
    raise ValueError(f"unsupported import format: {suffix}")


def manifest(command: str, source: pathlib.Path, outputs: list[pathlib.Path], converter: str, count: int | None) -> pathlib.Path:
    record = {
        "schema_version": 1,
        "operation": command,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": str(source),
        "source_sha256": sha256(source),
        "media_type": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
        "converter": converter,
        "item_count": count,
        "outputs": [{"path": str(item), "sha256": sha256(item)} for item in outputs],
    }
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    target = MANIFESTS / f"{source.stem}-{record['source_sha256'][:12]}-{command}.json"
    write_new(target, json.dumps(record, indent=2) + "\n")
    return target


def import_document(source: pathlib.Path) -> None:
    source = source.resolve(strict=True)
    digest = sha256(source)
    original = ORIGINALS / f"{digest[:12]}-{source.name}"
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    if not original.exists():
        shutil.copy2(source, original)
    elif sha256(original) != digest:
        raise ValueError(f"existing original does not match source digest: {original}")
    text, count, converter = extract(original)
    canonical = MARKDOWN / f"{source.stem}.md"
    write_new(canonical, f"# {source.stem}\n\n{text.strip()}\n")
    record = manifest("import", original, [canonical], converter, count)
    print(f"imported: {canonical.relative_to(ROOT)}; manifest: {record.relative_to(ROOT)}")


def markdown_html(text: str, title: str) -> str:
    blocks = []
    for line in text.splitlines():
        if line.startswith("# "):
            blocks.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            blocks.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            blocks.append(f"<p>{html.escape(line)}</p>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head><body>{''.join(blocks)}</body></html>"


def export_document(source: pathlib.Path, fmt: str) -> None:
    source = source.resolve(strict=True)
    if ROOT / "knowledge/markdown" not in source.parents:
        raise ValueError("exports must originate from knowledge/markdown")
    fmt = fmt.lower()
    if fmt not in {"pdf", "docx"}:
        raise ValueError("supported export formats are pdf and docx")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{source.stem}.{fmt}"
    if target.exists():
        raise ValueError(f"refusing to overwrite derived file: {target}")
    with tempfile.TemporaryDirectory(dir=ROOT / ".runtime") as tmp:
        html_path = pathlib.Path(tmp) / f"{source.stem}.html"
        html_path.write_text(markdown_html(source.read_text(), source.stem), encoding="utf-8")
        proc = subprocess.run(office_command("--convert-to", fmt, "--outdir", str(OUTPUT), str(html_path)), capture_output=True, text=True)
        if proc.returncode != 0 or not target.exists():
            raise ValueError(f"LibreOffice export failed: {proc.stderr or proc.stdout}")
    record = manifest("export", source, [target], "LibreOffice", None)
    print(f"exported: {target.relative_to(ROOT)}; manifest: {record.relative_to(ROOT)}")


def render_document(source: pathlib.Path) -> None:
    source = source.resolve(strict=True)
    if not source.is_relative_to(OUTPUT):
        raise ValueError("renders must originate from output/")
    render_dir = OUTPUT / "rendered" / source.stem
    if render_dir.exists():
        raise ValueError(f"refusing to overwrite render directory: {render_dir}")
    render_dir.mkdir(parents=True)
    pdf = source
    if source.suffix.lower() != ".pdf":
        proc = subprocess.run(office_command("--convert-to", "pdf", "--outdir", str(render_dir), str(source)), capture_output=True, text=True)
        pdf = render_dir / f"{source.stem}.pdf"
        if proc.returncode != 0 or not pdf.exists():
            raise ValueError(f"LibreOffice render failed: {proc.stderr or proc.stdout}")
    preview = render_dir / "preview.png"
    proc = subprocess.run(["/usr/bin/sips", "-s", "format", "png", str(pdf), "--out", str(preview)], capture_output=True, text=True)
    if proc.returncode != 0 or not preview.exists() or preview.stat().st_size == 0:
        raise ValueError(f"render inspection failed: {proc.stderr or proc.stdout}")
    record = manifest("render", source, [preview], "LibreOffice+sips", None)
    print(f"rendered: {preview.relative_to(ROOT)}; manifest: {record.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("import", "render"):
        item = sub.add_parser(name)
        item.add_argument("file")
    item = sub.add_parser("export")
    item.add_argument("file")
    item.add_argument("format")
    args = parser.parse_args()
    try:
        if args.command == "import": import_document(pathlib.Path(args.file))
        elif args.command == "export": export_document(pathlib.Path(args.file), args.format)
        else: render_document(pathlib.Path(args.file))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
