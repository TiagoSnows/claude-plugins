# Skill Arsenal — role → skill map (tuning reference)

The Coordinator consults this to "tune" itself and its workers: reach for the right installed skill at the right moment. **Extensible** — append rows as new skills are installed. A skill you name in a worker brief is loaded by that worker via its `Skill` tool.

## Where these skills live

Almost every skill below ships in the sibling **`tiago-skills`** plugin (same `tiago-plugins` marketplace as this one). Install both together:

```
/plugin marketplace add TiagoSnows/claude-plugins
/plugin install pbes@tiago-plugins
/plugin install tiago-skills@tiago-plugins
```

These are a **personal, adapted ecosystem** — many started as third-party skills (mostly MIT) and were tweaked; they may not behave identically to their originals. A few large packs are NOT bundled and stay as external installs (marked *(external)* below).

## Missing skill → WARN, never silently degrade

Every skill is an **enhancement, not a dependency**. If `tiago-skills` isn't installed, the pattern (plan → delegate → verify → synthesize) still works. But a skill you *wanted* and couldn't use is never swallowed silently — you tell the user.

1. **Check before naming.** Before putting a skill in a worker brief, confirm it appears in the session's available-skills list. Never name one you haven't seen listed.
2. **Absent skill → surface it, don't hide it.** When a skill that would have improved the sub-task is missing, emit an explicit warning to the user: which skill, what it would have done better here, and the exact install command (see table above). Do this the moment you notice — not buried in the final synthesis.

   > ⚠️ Skill `tdd` not installed — did this sub-task without test-first discipline. Install: `/plugin install tiago-skills@tiago-plugins`.

3. **Then proceed** with the worker's own judgment so the task still completes. Warning first, work second — never work-only.
4. **Never install autonomously** — the warning names the command; running it is always the user's explicit call.
5. A worker briefed with an unavailable skill must report that fact back so you can raise the warning; it must not fail silently or pretend it used the skill.

## Coordinator-level (you, the main loop — invoke these yourself)
These plan, interrogate, or fan out. Run them in the main loop; do NOT push them into a worker (several spawn their own agents, and workers can't nest). All in `tiago-skills` unless marked.

| Skill | Reach for it when |
|---|---|
| `grilling` / `grill-me` | Before fanning out a large/ambiguous/high-stakes task — stress-test goal, scope, success criteria first. |
| `domain-modeling` | Pinning domain terms / ubiquitous language / recording an ADR. |
| `codebase-design` | Designing a module's interface / seams before delegating the implementation. |
| `wayfinder` | Planning large work as investigation tickets on an issue tracker. |
| `to-spec` / `to-tickets` | Turning a settled plan into a spec, then into tracer-bullet tickets. |
| `triage` | Moving issues through a triage state machine. |
| `handoff` | Compacting the session into a faithful handoff doc (avoids inflated handoffs). |
| `research` | Multi-source investigation that itself fans out (coordinator territory). |
| `code-review` | Two-axis (standards + spec) review that spawns its own sub-agents. |
| `security-review` (built-in) | Reviewing a diff for vulnerabilities before merge. |

## Editor-worker-loadable (name in an editor-worker brief)
Must not fan out. Flag `[tool]` = needs a system tool installed to actually run (see below).

| Skill | Load it for | Deps |
|---|---|---|
| `tdd` | Implement a feature/bugfix test-first (red-green-refactor). | — |
| `test-fixing` | A suite has failing tests — group, patch, re-run. | — |
| `diagnosing-bugs` | Debug a failure; root-cause tracing. | — |
| `prototype` | Throwaway prototype to answer a design question. | — |
| `playwright-skill` | Write/run browser E2E tests. | `[tool]` Node + Chromium |
| `pict-test-designer` | Combinatorial (pairwise) test-case design. | `[tool]` PICT / `pypict` |
| `ffuf-skill` | Web fuzzing / pentest — **authorized targets only**. | `[tool]` `ffuf` binary |
| `impeccable` / `design-taste-frontend` / `high-end-visual-design` / `minimalist-ui` / `industrial-brutalist-ui` / `gpt-taste` | Frontend/UI design & polish. | — |
| `karpathy-guidelines` | General code-quality discipline on any edit. | — |

## Reader-worker-loadable (name in a reader-worker brief)
| Skill | Load it for | Deps |
|---|---|---|
| `postgres` | Read-only SQL inspection of a Postgres DB. | `[tool]` `pip psycopg2-binary` + local `connections.json` |

## Security / RE / Network (tool-heavy — usually editor worker, needs Bash)

| Skill | Load it for | Deps |
|---|---|---|
| `04-reverse-engineering` | Binary analysis, disassembly, decompilation, firmware & protocol RE. | `[tool]` Ghidra / x64dbg / objdump / Python — per task |
| `08-network-security` | Traffic/PCAP analysis, protocol decode, IDS/IPS rules, firewall & anomaly audit. | `[tool]` tshark / scapy / Python |

A reader worker can load these for pure static, Read-only analysis; use the editor worker when the task runs tools via Bash.

## Marketing / Growth (bundled in `tiago-skills`)

The 44-skill marketing pack ships inside `tiago-skills` (MIT © Corey Haines — see `NOTICE.md`). Editor-worker for copy/pages/config; coordinator for strategy. Names may resolve as bare (`copywriting`) or namespaced depending on install — check the available-skills list.

- **Copy & content:** `copywriting` · `copy-editing` · `content-strategy` · `marketing-ideas` · `social` · `video` · `image`
- **Landing / conversion:** `cro` · `popups` · `paywalls` · `signup` · `onboarding` · `lead-magnets` · `free-tools` · `pricing`
- **SEO & discovery:** `seo-audit` · `ai-seo` · `programmatic-seo` · `schema` · `site-architecture` · `aso` · `directory-submissions`
- **Ads & launch:** `ads` · `ad-creative` · `ab-testing` · `launch`
- **Email & outreach:** `emails` · `cold-email` · `sms` · `prospecting`
- **Growth & retention:** `churn-prevention` · `referrals` · `community-marketing` · `product-marketing` · `marketing-plan` · `marketing-psychology`
- **Sales / revops / research:** `sales-enablement` · `revops` · `customer-research`
- **Competitive & PR:** `competitor-profiling` · `competitors` · `public-relations` · `co-marketing`
- **Analytics:** `analytics`

**Sales-page recipe:** `copywriting` + a design skill (`impeccable` / `design-taste-frontend`) + `cro` + `marketing-psychology` + `seo-audit` / `schema`. Fan these across editor workers; you synthesize the final page.

## System-tool gate (no-autonomous-install rule)
These skills are files but stay **guidance-only until the tool is present**. Never auto-install; get explicit user consent first:
- `playwright-skill` → Node.js + `npm install` + `npx playwright install chromium` (~150MB). *(node_modules NOT shipped — run npm install after enabling.)*
- `pict-test-designer` → Microsoft PICT binary, or `pip install pypict`
- `postgres` → `pip install psycopg2-binary` + a local `connections.json` (copy from `connections.example.json`, chmod 600 — NEVER commit the real one)
- `ffuf-skill` → `ffuf` Go binary (a real network fuzzer — authorized targets only)

## How to use in a brief
> "…Load the `tdd` skill and implement X test-first. Return the distilled diff-receipt."
Name the skill explicitly — the worker won't guess. If the skill needs a gated tool that's absent, the worker reports back rather than failing silently.
