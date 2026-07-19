# DESIGN — Plan Big, Execute Small

Reusable orchestration artifact for Codex App and Claude Code.

## Source

The original pattern comes from Anthropic's
[Plan Big, Execute Small cookbook](https://github.com/anthropics/claude-cookbooks/blob/main/managed_agents/CMA_plan_big_execute_small.ipynb).
Its reference run reported approximately 2.5× lower cost, 3× higher speed, and
84% of input tokens at the worker rate. Those numbers describe that Claude
experiment only; they are not a Codex benchmark.

## Stable architecture

The visible main loop remains the coordinator because it owns requirements,
decisions, supervision, verification, and the final result. Bounded workers do
token-heavy reading or surgical edits and return distilled evidence.

The portable contract is:

1. define the outcome and observable completion criteria;
2. decompose only independent work;
3. dispatch one bounded assignment per worker;
4. wait for every terminal result;
5. distrust and verify reports;
6. synthesize only supported claims.

## Runtime adapters

The coordinator selects an adapter from the tools exposed in the current
session.

| Concern | Codex | Claude Code |
|---|---|---|
| Spawn | `spawn_agent` | `Agent` |
| Refine | `send_message` / `followup_task` | `SendMessage` |
| Wait | `wait_agent` plus terminal agent state | synchronous return or surfaced background completion |
| Reader | built-in `explorer` plus explicit no-edit brief | `pbes:pbes-reader` tool-scoped agent |
| Editor | built-in `worker` with owned files/worktree | `pbes:pbes-editor` tool-scoped agent |
| Models | capability-first routing from the current schema | packaged Sonnet default unless explicitly overridden |

The canonical details live in:

- `skills/plan-big-execute-small/references/codex-runtime.md`;
- `skills/plan-big-execute-small/references/claude-runtime.md`;
- `skills/plan-big-execute-small/references/model-routing.md`.

## Model policy

The canonical, capability-first policy lives in
`skills/plan-big-execute-small/references/model-routing.md`. This document does
not duplicate its model slugs or effort defaults. Runtime adapters must never
treat models from different providers as equal in price, latency, quality, or
context.

## Safety properties

1. Reader assignments prohibit edits and disclose whether that is enforced by
   tooling or only by instruction.
2. Concurrent editors receive non-overlapping ownership and isolated
   worktrees when the filesystem is shared.
3. Raw logs, captures, and large files stay outside the coordinator context.
4. No conclusion is drawn while requested workers remain active.
5. Infrastructure failures are re-dispatched or reported, never smoothed over.
6. Load-bearing facts receive direct or independent adversarial verification.

## Invocation

- Codex plugin: `$pbes:plan-big-execute-small`
- Claude plugin: `/pbes:plan-big-execute-small`

Implicit invocation is controlled by the skill description and applicable host
policy.
