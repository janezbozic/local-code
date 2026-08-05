# Milestone 3 dependency approval

The safe-web gateway uses only Python's standard library. SearXNG must be installed into `.venv/search` from an immutable upstream revision after compatibility with the local Python version is confirmed. Normal workbench operation never performs this installation or any dependency update.

The approved source revision is `c63835bd2a5133b30b3752a20eac6b443a918f41` from `https://github.com/searxng/searxng.git`. It is installed editable into `.venv/search` from `.tools/searxng`; all runtime requirements are exact pins from that revision. Wheels are downloaded to `.tools/wheels/search`, hashed locally, and installed with `--no-index --find-links` so normal installation and operation do not contact a package index.

Python 3.14 compatibility was demonstrated by successful wheel resolution, offline installation, and `searx.webapp` import. Upgrades remain manual and must repeat the pin and wheel-hash review.
