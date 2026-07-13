Marketplace pessoal de plugins para Claude Code.

## Plugins

### pbes — Plan Big, Execute Small

Padrão de orquestração baseado no cookbook da Anthropic ("Plan Big, Execute Small"): o modelo frontier (loop principal) vira **Coordenador** — planeja, delega, verifica e sintetiza — enquanto workers Sonnet baratos fazem a leitura/edição pesada em contextos isolados e devolvem só achados destilados (~300 tokens). Referência: ~2,5× mais barato, ~3× mais rápido.

Conteúdo:

| Componente | O que é |
|---|---|
| Skill `plan-big-execute-small` | Doutrina do Coordenador (plan → delegate → wait → verify → synthesize) |
| Agent `pbes:pbes-reader` | Worker Sonnet read-only (Read, Grep, Glob, WebFetch, Skill) |
| Agent `pbes:pbes-editor` | Worker Sonnet com escrita (Read, Edit, Write, Grep, Glob, Bash, Skill) |
| `references/skill-arsenal.md` | Mapa role→skill para "tunar" workers |
| `DESIGN.md` | Racional do design (mapeamento SDK → Claude Code, safeguards) |

## Instalação (em qualquer PC)

Dentro do Claude Code:

```
/plugin marketplace add TiagoSnows/claude-plugins
/plugin install pbes@tiago-plugins
```

Repo privado: o `gh`/git da máquina precisa estar autenticado na conta (`gh auth login`).

## Uso

A skill ativa sozinha em tarefas amplas (muitos arquivos/fontes), ou manualmente:

```
/pbes:plan-big-execute-small
```

> Nota: instalado via plugin, os agents são namespaced (`pbes:pbes-reader`). Se você também tiver cópias soltas em `~/.claude/agents/` e `~/.claude/skills/`, remova-as para não duplicar.
