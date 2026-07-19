---
name: plan-big-execute-small
description: Coordinate broad tasks by decomposing heavy reading, research, review, decoding, or multi-file work into focused subagent assignments, then verifying and synthesizing their distilled findings. Use when the user explicitly asks for subagents, delegation, parallel work, orchestration, or plan-big-execute-small, or when applicable project instructions explicitly require subagents and the task is genuinely broad. Supports Codex and Claude Code; do not use for small single-file or sequential tasks.
---

# Plan Big, Execute Small

Act as the coordinator for the remainder of the task. Keep bulk reading and
independent work in subagent contexts; retain planning, supervision,
verification, and synthesis in the main thread.

## Select the runtime adapter

Inspect the collaboration tools actually exposed in the current session.

- When `spawn_agent`, `send_message`, `followup_task`, and `wait_agent` are
  available, read and follow [codex-runtime.md](references/codex-runtime.md).
- When `Agent`, `SendMessage`, and the `pbes-reader` / `pbes-editor` agents are
  available, read and follow
  [claude-runtime.md](references/claude-runtime.md).
- Never invent a tool, agent profile, model slug, permission boundary, or
  concurrency limit. If neither adapter matches, state that PBES delegation is
  unavailable and continue with the host's normal sequential workflow. Do not
  pretend the delegation, report-review, or completion-barrier steps ran.

Read [model-routing.md](references/model-routing.md) before selecting explicit
models or reasoning effort.

## Core workflow

1. Define the outcome, scope, constraints, and observable completion criteria.
2. Stress-test an ambiguous or high-stakes plan before delegation. Use
   `grilling` only when clarification materially changes the work.
3. Decompose into independent, bounded assignments with one deliverable each.
4. Dispatch only assignments that can run independently.
5. Continue useful coordinator work while agents run without duplicating their
   bulk assignments.
6. Wait for every spawned agent before drawing the final conclusion.
7. Review each report critically. Re-dispatch vague, unsupported, stale, or
   off-scope work.
8. Verify load-bearing claims independently, adversarially when risk is high.
9. Synthesize only verified findings, cite evidence, and state unresolved
   uncertainty.

## Brief contract

Every assignment must contain:

- one objective;
- exact scope and explicit exclusions;
- required evidence pointers such as absolute `file:line`, command output, or
  primary-source URL;
- a concise return format, normally under 300 words and without raw dumps;
- a failure clause requiring uncertainty instead of guessing.

Assign by task boundary, not by prestige, price assumptions, or provider
analogies.

## Read and write isolation

For a reader assignment, explicitly prohibit edits and state that the
deliverable is a distilled evidence report. Do not claim that prose creates a
technical sandbox.

For an editor assignment:

- give ownership of specific files or a narrowly defined module;
- require preservation of unrelated user changes;
- follow repository branch and worktree rules;
- isolate concurrent editors in separate worktrees when the runtime shares a
  filesystem;
- never let two agents edit overlapping files concurrently;
- require tests or checks proportional to the change.

Use the least authority available. A read-only investigation does not
authorize edits, installs, external messages, or destructive operations.

## Context discipline

Do not pull large files, raw captures, long logs, or large web pages into the
coordinator context. Delegate bulk inspection and request distilled findings.
Directly inspect only small, targeted excerpts needed to verify a report.

The coordinator must still personally read selected skill instructions and
mandatory references when the host skill system requires it. Never delegate
that responsibility.

Consult [skill-arsenal.md](references/skill-arsenal.md) only when selecting
another skill for a concrete assignment.

## Verification

Treat agent reports as claims, not facts.

- Confirm that cited paths and lines exist.
- Check that reported commands actually support the conclusion.
- Use a second independent agent for a load-bearing claim when risk justifies
  the extra pass.
- Ask a verifier to refute the claim instead of repeating the first analysis.
- Re-run relevant tests or checks after integrating edits.
- Never fill an evidence gap with a plausible inference.

## Constraints

- Do not spawn agents unless the user, applicable project instructions, or
  this explicitly invoked skill authorizes delegation.
- Do not delegate sequential work merely to appear parallel.
- Do not conclude from partial reports while agents remain active.
- Do not use subagents for trivial, single-step work.
- Do not transplant benchmark claims between providers or runtimes.
- Higher-priority system, developer, user, and repository instructions always
  win.
