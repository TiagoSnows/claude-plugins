Marketplace pessoal de plugins para Claude Code. **Público.**

## Instalação

Dentro do Claude Code:

```
/plugin marketplace add TiagoSnows/claude-plugins
/plugin install pbes@tiago-plugins
```

Um comando traz tudo: a orquestração, os dois agents e todas as skills.

## Plugin: pbes — Plan Big, Execute Small + arsenal

Um plugin único que junta o padrão de orquestração da Anthropic com um arsenal de ~95 skills embutido.

**Como funciona:** o modelo frontier (loop principal) vira **Coordenador** — planeja, delega, verifica e sintetiza — enquanto workers Sonnet baratos (`pbes:pbes-reader` read-only e `pbes:pbes-editor` write) fazem a leitura/edição pesada em contextos isolados e devolvem só achados destilados (~300 tokens). Referência: ~2,5× mais barato, ~3× mais rápido. Os workers carregam qualquer skill do próprio plugin via `Skill` tool — o Coordenador só precisa nomear a skill no brief.

| Componente | O que é |
|---|---|
| Skill `plan-big-execute-small` | Doutrina do Coordenador (plan → delegate → wait → verify → synthesize) |
| Agent `pbes:pbes-reader` | Worker Sonnet read-only (Read, Grep, Glob, WebFetch, Skill) |
| Agent `pbes:pbes-editor` | Worker Sonnet com escrita (Read, Edit, Write, Grep, Glob, Bash, Skill) |
| `pbes/skills/*` | ~95 skills que os workers carregam sob demanda |
| `pbes/skills/plan-big-execute-small/references/skill-arsenal.md` | Mapa role→skill para "tunar" workers |

**Arsenal (~95 skills):** design (`impeccable`, `design-taste-frontend`, `minimalist-ui`…), testing (`tdd`, `test-fixing`, `pict-test-designer`), debugging (`diagnosing-bugs`), planejamento (`grilling`, `wayfinder`, `to-spec`), RE/security (`04-reverse-engineering`, `08-network-security`, `ffuf-skill`), DB (`postgres`), marketing (44 — `copywriting`, `ads`, `cro`, `seo-audit`…), code-quality (`karpathy-guidelines`), e mais.

**Ecossistema próprio adaptado** — muitas skills nasceram como skills de terceiros (majoritariamente MIT) e foram ajustadas; **podem não se comportar 100% igual às originais**. Atribuição e licenças em [`pbes/NOTICE.md`](pbes/NOTICE.md).

**Skills com dependência de tool de sistema** (guidance-only até instalar — nunca auto-instala):
- `playwright-skill` → `node_modules` NÃO vai no repo; rode `npm install` + `npx playwright install chromium`
- `pict-test-designer` → PICT binary ou `pip install pypict`
- `postgres` → `pip install psycopg2-binary` + copie `connections.example.json` → `connections.json` (nunca commite o real)
- `ffuf-skill` → binário `ffuf` (só alvos autorizados)

## Uso

A skill do pbes ativa sozinha em tarefas amplas (muitos arquivos/fontes), ou manualmente:

```
/pbes:plan-big-execute-small
```

Quando uma skill do arsenal ajudaria mas não está instalada, o Coordenador **avisa** (qual skill, o que melhoraria, comando de install) — nunca degrada em silêncio nem instala sozinho.

## Custo de contexto

- **Índice sempre-ativo** (~95 descriptions): ~11k tokens, pagos ao instalar, em toda sessão.
- **Ativar o pbes**: +~2,6k tokens no loop principal (o `SKILL.md`). O arsenal completo só carrega se o Coordenador o ler.
- **Workers**: corpo do agent + conteúdo pesado ficam no contexto isolado deles; o loop principal recebe só o report (~300 tokens/worker).

## Desenvolvimento

Cópia editável em `~/.claude/plugins-dev/claude-plugins`. Edita → commita → push. Outras máquinas: `/plugin marketplace update tiago-plugins`.
