Marketplace pessoal de plugins para Claude Code. **Público.**

## Instalação

Dentro do Claude Code:

```
/plugin marketplace add TiagoSnows/claude-plugins
/plugin install pbes@tiago-plugins
/plugin install tiago-skills@tiago-plugins
```

## Plugins

### pbes — Plan Big, Execute Small

Padrão de orquestração baseado no cookbook da Anthropic: o modelo frontier (loop principal) vira **Coordenador** — planeja, delega, verifica e sintetiza — enquanto workers Sonnet baratos fazem a leitura/edição pesada em contextos isolados e devolvem só achados destilados (~300 tokens). Referência: ~2,5× mais barato, ~3× mais rápido.

| Componente | O que é |
|---|---|
| Skill `plan-big-execute-small` | Doutrina do Coordenador (plan → delegate → wait → verify → synthesize) |
| Agent `pbes:pbes-reader` | Worker Sonnet read-only (Read, Grep, Glob, WebFetch, Skill) |
| Agent `pbes:pbes-editor` | Worker Sonnet com escrita (Read, Edit, Write, Grep, Glob, Bash, Skill) |
| `references/skill-arsenal.md` | Mapa role→skill para "tunar" workers (aponta para `tiago-skills`) |

### tiago-skills — coleção de skills

~50 skills: design (`impeccable`, `design-taste-frontend`, `minimalist-ui`…), testing (`tdd`, `test-fixing`, `pict-test-designer`), debugging (`diagnosing-bugs`), planejamento (`grilling`, `wayfinder`, `to-spec`), RE/security (`04-reverse-engineering`, `08-network-security`, `ffuf-skill`), DB (`postgres`), e mais.

**Ecossistema próprio adaptado** — muitas nasceram como skills de terceiros (majoritariamente MIT) e foram ajustadas; **podem não se comportar 100% igual às originais**. Direitos de cada skill de terceiros pertencem aos autores originais sob suas licenças.

**Não incluído** (instala à parte, packs grandes):
- `marketing-skills:*` (44 skills) → `/plugin marketplace add coreyhaines31/marketingskills`
- `karpathy-guidelines` → `/plugin marketplace add forrestchang/andrej-karpathy-skills`

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

## Desenvolvimento

Cópia editável em `~/.claude/plugins-dev/claude-plugins`. Edita → commita → push. Outras máquinas: `/plugin marketplace update tiago-plugins`.
