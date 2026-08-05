# Document lifecycle

The preserving workflow is `original → extraction → canonical Markdown → export → render → inspection`.
Imports copy the source into `knowledge/originals`, create a new canonical file in
`knowledge/markdown`, and write a checksum manifest in `knowledge/manifests`.
Exports and renders go only to `output`. Existing canonical or derived files are
never overwritten.

The Python environment is project-local at `.venv/documents`. Its direct pins are
in `config/documents/requirements.in`; reviewed direct-wheel SHA-256 values are
in `config/versions.env`. The resolved wheel cache lives below
`.tools/wheels/documents` and is excluded from Git.

## Supported workflows

| Input or operation | Result |
|---|---|
| PDF import | Canonical Markdown, manifest, and recorded page count |
| DOCX import | Canonical Markdown, manifest, and recorded page count |
| PPTX import | Canonical Markdown, manifest, and recorded slide count |
| XLSX import | Canonical Markdown, manifest, and recorded sheet count |
| Markdown export | A new PDF or DOCX in `output` |
| PDF render | Non-empty rendered inspection artifacts in `output` |

## Commands

```sh
make document-import FILE=/absolute/path/source.docx
make document-export FILE=knowledge/markdown/source.md FORMAT=pdf
make document-render FILE=output/source.pdf
```

All paths are interpreted from the repository root except the import source,
which must be an explicit source file. Existing canonical or derived files are
never overwritten.

## Provenance

PDF, DOCX, PPTX, and XLSX imports record their page, slide, or sheet counts.
Rendered output must exist and be non-empty before the operation succeeds.
Manifests also preserve source hashes, media type, converter identity, timestamp,
and generated paths.

## Privacy

`knowledge/originals` and `output` are ignored by Git. Before publishing a
canonical Markdown file or manifest, review it for private text, filenames,
identifiers, and metadata. Conversion does not make content safe to publish.
