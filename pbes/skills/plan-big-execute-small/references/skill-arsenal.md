# Skill Arsenal — role → skill map (tuning reference)

The Coordinator consults this to "tune" itself and its workers: reach for the right installed skill at the right moment. **Extensible** — append rows as new skills are installed. A skill you name in a worker brief is loaded by that worker via its `Skill` tool.

## Coordinator-level (you, the main loop — invoke these yourself)
These plan, interrogate, or fan out. Run them in the main loop; do NOT push them into a worker (several spawn their own agents, and workers can't nest).

| Skill | Reach for it when |
|---|---|
| `grilling` / `grill-me` | Before fanning out a large/ambiguous/high-stakes task — stress-test goal, scope, success criteria first. |
| `domain-modeling` | Pinning domain terms / ubiquitous language / recording an ADR. |
| `codebase-design` | Designing a module's interface / seams before delegating the implementation. |
| `wayfinder` | Planning large work as investigation tickets on an issue tracker. |
| `to-spec` / `to-tickets` | Turning a settled plan into a spec, then into tracer-bullet tickets. |
| `triage` | Moving issues through a triage state machine. |
| `handoff` | Compacting the session into a faithful handoff doc (use this instead of hand-writing resume notes — it avoids inflated handoffs). |
| `research` / `deep-research` | Multi-source investigation that itself fans out (coordinator territory). |
| `code-review` | Two-axis (standards + spec) review that spawns its own sub-agents. |
| `security-review` | Reviewing a diff for vulnerabilities before merge. |

## Editor-worker-loadable (name in a `pbes-editor` brief)
Must not fan out. Flag `[tool]` = needs a system tool installed to actually run (see below).

| Skill | Load it for | Deps |
|---|---|---|
| `tdd` | Implement a feature/bugfix test-first (red-green-refactor). | — |
| `test-fixing` | A suite has failing tests — group, patch, re-run. | — |
| `diagnosing-bugs` / `systematic-debugging` | Debug a failure; `systematic-debugging` bundles the root-cause-tracing technique. | — |
| `prototype` | Throwaway prototype to answer a design question. | — |
| `playwright-skill` | Write/run browser E2E tests. | `[tool]` Node + Chromium |
| `pict-test-designer` | Combinatorial (pairwise) test-case design. | `[tool]` PICT / `pypict` |
| `ffuf-skill` | Web fuzzing / pentest — **authorized targets only**. | `[tool]` `ffuf` binary |
| `impeccable` / `design-taste-frontend` / `high-end-visual-design` / `minimalist-ui` / `industrial-brutalist-ui` / `gpt-taste` | Frontend/UI design & polish. | — |
| `karpathy-guidelines` | General code-quality discipline on any edit. | — |

## Reader-worker-loadable (name in a `pbes-reader` brief)
| Skill | Load it for | Deps |
|---|---|---|
| `postgres` | Read-only SQL inspection of a Postgres DB. | `[tool]` `pip psycopg2-binary` + `connections.json` |

## Security / RE / Network (tool-heavy — usually `pbes-editor`, needs Bash)

| Skill | Load it for | Deps |
|---|---|---|
| `04-reverse-engineering` | Binary analysis, disassembly, decompilation, firmware & **protocol RE** (Mir4G client, packet cipher, opcode maps). | `[tool]` Ghidra / x64dbg / objdump / Python — per task |
| `08-network-security` | Traffic/PCAP analysis, protocol decode, IDS/IPS rules, firewall & anomaly audit. | `[tool]` tshark / scapy / Python |

A `pbes-reader` can load these for pure static, Read-only analysis; use `pbes-editor` when the task runs tools via Bash. `ffuf-skill` (web pentest, above) is part of this family.

## Marketing / Growth (`marketing-skills:*` — editor-worker for copy/pages/config, coordinator for strategy)

Full pack (44). Pick by lane; prefix every name with `marketing-skills:`. The orchestrator decides which fits the request.

- **Copy & content:** `copywriting` · `copy-editing` · `content-strategy` · `marketing-ideas` · `social` · `video` · `image`
- **Landing / conversion:** `cro` · `popups` · `paywalls` · `signup` · `onboarding` · `lead-magnets` · `free-tools` · `pricing`
- **SEO & discovery:** `seo-audit` · `ai-seo` · `programmatic-seo` · `schema` · `site-architecture` · `aso` · `directory-submissions`
- **Ads & launch:** `ads` · `ad-creative` · `ab-testing` · `launch`
- **Email & outreach:** `emails` · `cold-email` · `sms` · `prospecting`
- **Growth & retention:** `churn-prevention` · `referrals` · `community-marketing` · `product-marketing` · `marketing-plan` · `marketing-psychology`
- **Sales / revops / research:** `sales-enablement` · `revops` · `customer-research`
- **Competitive & PR:** `competitor-profiling` · `competitors` · `public-relations` · `co-marketing`
- **Analytics:** `analytics`

**Sales-page recipe:** `copywriting` (copy) + a design skill (`impeccable` / `design-taste-frontend`) for the page build + `cro` (conversion) + `marketing-psychology` (persuasion) + `seo-audit` / `schema` (discoverability). Fan these across editor workers; you synthesize the final page.

## System-tool gate (per user's no-autonomous-install rule)
These skills are installed as files but stay **guidance-only until the tool is present**. Never auto-install; get explicit user consent first:
- `playwright-skill` → Node.js + `npm install` + `npx playwright install chromium` (~150MB)
- `pict-test-designer` → Microsoft PICT binary, or `pip install pypict`
- `postgres` → `pip install psycopg2-binary` + a local `connections.json` (chmod 600)
- `ffuf-skill` → `ffuf` Go binary (a real network fuzzer — authorized targets only)

## How to use in a brief
> "…Load the `tdd` skill and implement X test-first. Return the distilled diff-receipt."
Name the skill explicitly — the worker won't guess. If the skill needs a gated tool that's absent, the worker reports back rather than failing silently.
