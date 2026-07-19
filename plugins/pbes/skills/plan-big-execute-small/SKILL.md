---
name: plan-big-execute-small
description: Coordinate broad tasks by decomposing heavy reading, research, review, decoding, or multi-file work into focused subagent assignments, then verifying and synthesizing their distilled findings. Use when the user explicitly asks for subagents, delegation, parallel work, orchestration, or plan-big-execute-small, or when applicable project instructions explicitly require subagents and the task is genuinely broad. Do not use for small single-file or sequential tasks.
---

# Plan Big, Execute Small

Act as the coordinator for the remainder of the task. Keep bulk reading and
independent work in subagent contexts; retain planning, supervision,
verification, and synthesis in the main thread.

Read and follow [codex-runtime.md](references/codex-runtime.md). Read
[model-routing.md](references/model-routing.md) before selecting explicit
models or reasoning effort. Consult
[skill-arsenal.md](references/skill-arsenal.md) only when selecting another
installed skill for a concrete assignment.

If the required Codex collaboration tools are not exposed, state that PBES
delegation is unavailable and continue with the host's normal sequential
workflow. Do not pretend delegation, report review, or completion barriers ran.

## Workflow

1. Define the outcome, scope, constraints, and observable completion criteria.
2. Stress-test an ambiguous or high-stakes plan before delegation when
   clarification materially changes the work.
3. Decompose into independent, bounded assignments with one deliverable each.
4. Dispatch only assignments that can run independently.
5. Continue useful coordinator work without duplicating subagent assignments.
6. Wait for every spawned agent before drawing the final conclusion.
7. Review each report critically. Re-dispatch vague, unsupported, stale, or
   off-scope work.
8. Verify load-bearing claims independently, adversarially when risk is high.
9. Synthesize only verified findings, cite evidence, and state uncertainty.

## Brief contract

Every assignment must contain:

- one objective;
- exact scope and explicit exclusions;
- required evidence such as absolute `file:line`, command output, or a
  primary-source URL;
- a concise return format, normally under 300 words without raw dumps;
- a failure clause requiring uncertainty instead of guessing.

Assign by task boundary, not by prestige, price assumptions, or provider
analogies.

## Read and write isolation

For a reader assignment, explicitly prohibit edits and require a distilled
evidence report. Do not claim that prose creates a technical sandbox.

For an editor assignment:

- give ownership of specific files or a narrowly defined module;
- require preservation of unrelated user changes;
- follow repository branch and worktree rules;
- isolate concurrent editors in separate worktrees when the filesystem is
  shared;
- never let two agents edit overlapping files concurrently;
- require tests or checks proportional to the change.

Use the least authority available. A read-only investigation does not
authorize edits, installs, external messages, or destructive operations.

## Context discipline

Delegate bulk inspection of large files, raw captures, logs, and web pages.
Request distilled findings and directly inspect only small excerpts needed to
verify a report.

The coordinator must personally read selected skill instructions and mandatory
references when the host skill system requires it. Never delegate that
responsibility.

## Verification

Treat agent reports as claims, not facts.

- Confirm cited paths and lines.
- Check that commands support the reported conclusion.
- Use a second independent agent for load-bearing claims when risk justifies
  the extra pass.
- Ask a verifier to refute the claim instead of repeating the first analysis.
- Re-run relevant checks after integrating edits.
- Never fill an evidence gap with a plausible inference.

## Constraints

- Do not spawn agents unless the user, applicable project instructions, or
  this explicitly invoked skill authorizes delegation.
- Do not delegate sequential work merely to appear parallel.
- Do not conclude from partial reports while agents remain active.
- Do not use subagents for trivial, single-step work.
- Do not transplant benchmark claims between providers or runtimes.
- Higher-priority instructions always win.
