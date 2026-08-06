#!/usr/bin/env python3
"""Policy unit tests for the preserving document workflow."""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import tempfile
import unittest
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow", ROOT / "tools/documents/workflow.py")
workflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(workflow)


class DocumentPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = pathlib.Path(tempfile.mkdtemp(prefix="local-workbench-doc-policy-"))
        self.stem = f"policy-{uuid.uuid4().hex}"
        self.created: list[pathlib.Path] = []

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)
        for path in self.created:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    def test_import_rejects_mismatched_existing_original(self) -> None:
        source = self.work / f"{self.stem}.txt"
        source.write_text("canonical source text\n", encoding="utf-8")
        digest = workflow.sha256(source)
        original = workflow.ORIGINALS / f"{digest[:12]}-{source.name}"
        workflow.ORIGINALS.mkdir(parents=True, exist_ok=True)
        original.write_text("planted original bytes\n", encoding="utf-8")
        self.created.append(original)
        with self.assertRaisesRegex(ValueError, "does not match source digest"):
            workflow.import_document(source)

    def test_import_reuses_matching_original(self) -> None:
        source = self.work / f"{self.stem}.txt"
        source.write_text("matching source text\n", encoding="utf-8")
        digest = workflow.sha256(source)
        original = workflow.ORIGINALS / f"{digest[:12]}-{source.name}"
        workflow.ORIGINALS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, original)
        canonical = workflow.MARKDOWN / f"{source.stem}.md"
        try:
            workflow.import_document(source)
            self.assertTrue(canonical.is_file())
            manifests = list(workflow.MANIFESTS.glob(f"{original.stem}-*-import.json"))
            self.assertEqual(len(manifests), 1)
            self.created.extend([canonical, original, manifests[0]])
        except Exception:
            self.created.extend([canonical, original])
            raise

    def test_render_requires_output_path(self) -> None:
        outside = self.work / f"{self.stem}.pdf"
        outside.write_bytes(b"%PDF-1.4")
        with self.assertRaisesRegex(ValueError, "originate from output"):
            workflow.render_document(outside)

    def test_export_requires_markdown_path(self) -> None:
        outside = self.work / f"{self.stem}.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "knowledge/markdown"):
            workflow.export_document(outside, "pdf")


if __name__ == "__main__":
    unittest.main()
