# DESIGN — Plan Big, Execute Small (global artifact)

Reusable orchestration artifact for Claude Code. Global scope (`~/.claude/`), works across all Claude Code surfaces: CLI, desktop app, web, IDE.

## Source

Anthropic cookbook — "Plan Big, Execute Small" (Coordinated Managed Agents):
https://github.com/anthropics/claude-cookbooks/blob/main/managed_agents/CMA_plan_big_execute_small.ipynb

Frontier coordinator + cheap workers. Coordinator plans/delegates/synthesizes and holds no tools; workers do the token-heavy reading in isolated contexts and report distilled findings back. Reference run: ~2.5× cheaper, ~3× faster, 84% of input tokens at the worker rate.

## Why the coordinator is the main loop, not an agent

The cookbook is written for the **Claude Agent SDK**, where code (`client.beta.agents.create`) instantiates a coordinator agent and worker agents, and the coordinator gets automatic `create_agent` / `send_to_agent` / `wait_for_agents` tools.

Claude Code has no coordinator-that-spawns-coordinators primitive — subagent nesting is blocked. So the coordinator cannot be a subagent (a subagent can't fan out). It must be the **main loop wearing the coordinator persona**, and that persona is delivered by a **Skill** — the same mechanism that lets a persona take over the chat and persist across turns. This is also better for the user: the planning and steering happen in the visible main loop, where the user can intervene, instead of hidden inside an isolated agent.

The workers stay as real agents — this half maps 1:1 to the cookbook.

## SDK → Claude Code mapping

| Cookbook (SDK) | Claude Code |
|---|---|
| Coordinator agent (`agents.create`, model=frontier) | Main loop (Fable 5) + `plan-big-execute-small` skill as its system prompt |
| `create_agent` / `send_to_agent` (dynamic) | `Agent` tool (`model: "sonnet"`, `subagent_type`) + `SendMessage` |
| Deterministic fan-out + loops | `Workflow` tool (`agent({model:"sonnet", agentType, schema})`, `parallel`/`pipeline`) — requires user opt-in |
| Worker agents (model=Sonnet), tool-scoped | `pbes-reader` (read-only) / `pbes-editor` (write) subagents |
| `wait_for_agents` before concluding | await the Agent calls / `parallel()` barrier |
| Re-assign sub-question to fresh worker on infra error | re-dispatch / `.filter(Boolean)` |
| Worker `submit_result` (distilled) | worker's final message = distilled findings, ≤~300 tokens |

## Safeguards (from the cookbook, verbatim-distilled)

1. **Worker least-privilege** — "the blast radius you want": workers read untrusted input; scoping keeps the cheap model out of bash/filesystem. Coordinator holds ~no tools.
2. **Coordinator never reads raw content** — only distilled summaries.
3. **Context isolation** — the giant pages/files a worker reads never enter anyone else's context.
4. **Barrier before conclusion** — always wait for all spawned workers before synthesizing.
5. **Re-spawn on infra error** — rate limit / timeout → fresh worker, same sub-task.
6. **Verify** — every load-bearing fact confirmed from ≥2 independent workers/sources; adversarial refute-brief for high-stakes claims.

Plus one Claude-Code-specific hardening driven by the user's past pain (generic agent rubber-stamping bad worker output): the skill makes distrust-and-verify an explicit, non-optional step, and pins coordinator identity/persistence so the main loop does not silently revert to doing the work itself.

## Files

```
~/.claude/skills/plan-big-execute-small/SKILL.md    coordinator doctrine (the persona)
~/.claude/skills/plan-big-execute-small/DESIGN.md    this file
~/.claude/agents/pbes-reader.md                      read-only Sonnet worker
~/.claude/agents/pbes-editor.md                      write-capable Sonnet worker
```

## Invocation

Auto-trigger via the skill `description`, explicit `/plan-big-execute-small`, or natural language ("orchestrate this with workers"). On invoke, the main loop adopts the Coordinator persona and holds it until the task completes.
