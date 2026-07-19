# Codex runtime adapter

Use this adapter only when the current session exposes Codex collaboration
tools.

## Capacity

Discover the current concurrency budget from the session metadata or agent
tool description. The root coordinator consumes one slot. Never preserve an
old hard-coded limit when the runtime reports a different capacity.

Use fewer agents than the maximum when assignments are small, sequential, or
write-heavy. Batch excess assignments and keep a completion barrier between
dependent batches.

## Tool mapping

| Operation | Codex tool |
|---|---|
| Start an independent assignment | `spawn_agent` |
| Refine a running assignment | `send_message` |
| Give an idle agent another turn | `followup_task` |
| Stop current work without deleting the agent | `interrupt_agent` |
| Inspect team state | `list_agents` |
| Wait for mailbox or completion updates | `wait_agent` |

Prefer the built-in `explorer` role for specific read-heavy codebase questions
and `worker` for bounded implementation. Use another surfaced role only when
its documented contract fits the assignment.

## Fork and model overrides

When the tool schema permits model overrides only with a limited fork:

- use `fork_turns: "none"` for isolated assignments whose brief contains all
  required context;
- use a small positive fork when recent conversation context is essential;
- use full-history inheritance only when necessary, and omit incompatible
  model overrides.

Treat the callable tool schema as the authority for valid model slugs and
reasoning values.

## Filesystem and permissions

Codex agents may share the same filesystem and inherit the parent permission
mode. A reader brief that says "do not edit" is a behavioral constraint, not a
permission boundary.

For concurrent writers, use separate worktrees and non-overlapping ownership.
Tell every worker that it is not alone in the codebase and must preserve and
accommodate other changes.

## Skill loading

The coordinator personally reads every selected `SKILL.md` and mandatory
reference before acting. Do not assume a child can satisfy the coordinator's
skill-loading obligation.

Pass the assignment-relevant constraints from the selected skill in the brief.
Do not ask a child to spawn nested agents when the runtime depth limit prevents
it.

## Suggested briefs

### Reader

> Objective: answer one concrete question. Scope: inspect only the listed
> files/directories; do not edit anything. Return under 300 words with the
> conclusion, absolute file:line evidence, checks performed, and remaining
> uncertainty. If evidence is insufficient, say so and do not guess.

### Editor

> Objective: implement one bounded change. Scope: own only the listed
> files/module; preserve unrelated changes and follow branch/worktree rules.
> You are not alone in the codebase; accommodate concurrent changes and do not
> revert them. Run the named checks. Return a concise diff receipt listing
> changed files, verification results, and unresolved risks.

### Adversarial verifier

> Independently try to refute the stated claim. Do not rely on the first
> agent's reasoning. Inspect the primary evidence and report whether the claim
> holds, with precise pointers. Do not edit files.
