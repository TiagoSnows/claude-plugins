# Claude Code runtime adapter

Use this adapter only when Claude Code exposes the `Agent` tool and the PBES
custom agents.

## Workers

| Worker | Agent type | Use for |
|---|---|---|
| Reader | `pbes:pbes-reader` | Research, code exploration, decode, review, and document synthesis |
| Editor | `pbes:pbes-editor` | Surgical changes that require write or execute tools |

If agents are installed standalone, use the unnamespaced names surfaced by the
runtime.

## Dispatch

Use `Agent` for actively coordinated batches. Launch independent assignments
concurrently, prefer background execution for long work, and use
`SendMessage` to refine a running worker.

For synchronous calls, the returned result is the completion barrier. For
background calls, record every worker identifier and do not synthesize until
the runtime has surfaced a terminal result for each one. Use the current
runtime's status or wait surface when available. If no completion observation
exists, do not dispatch that assignment in the background.

Use `Workflow` only when it is actually available and the user explicitly
authorized that surface. Do not describe it as a Codex capability.

Discover the current worker capacity instead of assuming an old fixed number.
The packaged agents pin `sonnet` as their Claude default. Preserve that default
unless the current Claude runtime explicitly accepts a per-call override and
the task or user selected another model. Do not copy Codex model slugs into
Claude agent calls.

## Isolation

The packaged reader has a deliberately smaller tool list. The editor can write
and execute, so give it surgical ownership. Isolate parallel editors in
separate worktrees and never assign overlapping files.

## Skill loading

When the host exposes the `Skill` tool to custom agents, name an installed
skill in the worker brief so it can load the relevant instructions. Do not ask
a worker to load a fan-out skill when nesting is unavailable.

If a useful skill is missing, warn the user and continue with bounded
judgment. Never install it autonomously.
