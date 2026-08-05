# Bounded agents

`opencode.json` defines one primary coordinator and five subagents. Inference is
serialized by llama.cpp (`--parallel 1`), and subagents cannot delegate again.

## Roles

- `coordinator`: reads, delegates one level, reviews evidence, and decides. It
  cannot use web tools directly.
- `researcher`: can use only the `local-safe-web` MCP tool namespace.
- `explorer`: read/glob/grep inspection only.
- `implementer`: repository reads and scoped edits; web and delegation denied.
- `reviewer`: read/glob/grep inspection only.
- `document-specialist`: reads broadly but writes only canonical Markdown,
  manifests, and output paths.

The global permission policy asks for unspecified operations, denies external
directories and built-in web access, and denies reads of environment files.
Only the researcher may call the `local-safe-web` MCP namespace. The operating
system network sandbox remains authoritative even if an application permission
is configured incorrectly.

## Worktree handoff

The coordinator chooses a short branch name and creates a worktree manually:

    git worktree add .runtime/worktrees/TASK -b agent/TASK

One implementer owns that worktree. Before integration, the coordinator runs
checks there, reviews `git diff main...agent/TASK`, and asks the reviewer to
inspect the same diff. Integration is a reviewed merge from the main worktree.
Only after the merge and a clean status may the coordinator remove the worktree
with `git worktree remove .runtime/worktrees/TASK` and delete the branch. No
worktree arrangement implies parallel inference; the single llama slot remains
the hard serialization boundary.

Worktree creation and deletion are manual operations. Agent configuration does
not grant permission to remove branches, overwrite unrelated changes, or bypass
review.
