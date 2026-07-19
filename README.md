# Tiago Plugins

Marketplace público de plugins para Codex App e Claude Code.

## Plugin PBES

`pbes` significa **Plan Big, Execute Small**. O coordenador decompõe trabalhos
amplos, delega investigações ou edições delimitadas, espera todos os resultados,
verifica as evidências e só então sintetiza.

O marketplace entrega duas distribuições com o mesmo nome público. Ambas
contêm aproximadamente 90 skills de design, testes, debugging, planejamento,
reverse engineering, segurança, banco de dados e marketing. A árvore Claude é
a fonte canônica; a árvore Codex é uma projeção gerada com frontmatter
compatível com o App.

### Codex App e CLI

Adicione o marketplace versionado:

```powershell
codex plugin marketplace add TiagoSnows/claude-plugins --ref main
codex plugin add pbes@tiago-plugins
```

No Codex App, reinicie o aplicativo depois de adicionar o marketplace, abra
**Plugins**, selecione **Tiago Plugins** e instale **PBES**. Teste a atualização
em uma nova task para que a lista de skills seja recarregada.

O adaptador Codex usa as ferramentas de colaboração realmente expostas na
sessão. Ele descobre a capacidade concorrente, usa agentes `explorer` e
`worker`, respeita filesystem compartilhado e não promete isolamento que o
runtime não oferece.

Política preferida de modelos:

- coordenador e verificador crítico: Sol com esforço High;
- worker claro e repetível: Luna com Extra High quando Luna for chamável;
- fallback atual para runtimes sem Luna em `spawn_agent`: Terra, começando em
  Medium e aumentando o esforço somente quando necessário.

Os slugs são validados contra o schema da sessão. A skill não inventa um modelo
indisponível nem trata modelos de fornecedores diferentes como equivalentes.

### Claude Code

Dentro do Claude Code:

```text
/plugin marketplace add TiagoSnows/claude-plugins
/plugin install pbes@tiago-plugins
```

O adaptador Claude preserva os agents `pbes:pbes-reader` e
`pbes:pbes-editor`, incluindo suas superfícies distintas de ferramentas.

## Componentes

| Componente | Função |
|---|---|
| `plugins/pbes` | Distribuição Codex gerada e validada, com o arsenal completo |
| `pbes` | Distribuição Claude com agents e arsenal |
| `plan-big-execute-small` | Doutrina: planejar, delegar, esperar, verificar e sintetizar |
| `references/codex-runtime.md` | Mapeamento nativo para colaboração no Codex |
| `references/claude-runtime.md` | Mapeamento da distribuição Claude |
| `references/model-routing.md` | Política capability-first de modelos |
| `pbes/agents/*` | Agents reader/editor exclusivos do Claude |
| `pbes/skills/*` | Arsenal de skills carregadas sob demanda |

O resultado histórico de aproximadamente 2,5× menos custo e 3× mais velocidade
pertence ao experimento de referência no Claude. Ele não é apresentado como
benchmark do Codex.

## Uso

No Codex, invoque a skill pelo namespace do plugin:

```text
$pbes:plan-big-execute-small
```

No Claude Code:

```text
/pbes:plan-big-execute-small
```

Exemplo:

```text
Use $pbes:plan-big-execute-small para revisar arquitetura, testes e riscos desta
mudança em paralelo. Espere todos os agentes e verifique os achados antes de
concluir.
```

## Arsenal dual-runtime e dependências

O arsenal distribuído nos dois pacotes inclui design
(`impeccable`, `design-taste-frontend`,
`minimalist-ui`), testes (`tdd`, `test-fixing`, `pict-test-designer`),
debugging (`diagnosing-bugs`), planejamento (`grilling`, `wayfinder`,
`to-spec`), RE/segurança (`04-reverse-engineering`, `08-network-security`,
`ffuf-skill`), PostgreSQL e marketing.

Algumas skills precisam de ferramentas externas e permanecem apenas como
guidance até a instalação explícita:

- `playwright-skill`: Node.js e Chromium;
- `pict-test-designer`: PICT ou `pypict`;
- `postgres`: `psycopg2-binary` e configuração local nunca versionada;
- `ffuf-skill`: binário `ffuf`, somente para alvos autorizados.

Muitas skills foram adaptadas de projetos de terceiros. Consulte
[pbes/NOTICE.md](pbes/NOTICE.md) para procedência e licenças.

`pbes/skills` permanece intocado como contrato Claude. A geração copia somente
arquivos rastreados pelo Git, ignora caches e arquivos sensíveis e converte cada
`SKILL.md` para o contrato Codex. Campos exclusivos do Claude, como
`disable-model-invocation` e `argument-hint`, são preservados sob
`metadata.claude` na projeção. O Codex não implementa esses controles de
invocação; portanto, eles são informativos no pacote Codex e continuam
funcionais somente no pacote Claude.

## Desenvolvimento

Cada runtime possui manifesto próprio:

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
pbes/.claude-plugin/plugin.json
plugins/pbes/.codex-plugin/plugin.json
```

Valide a skill e os dois contratos antes de publicar. Não versione credenciais,
conexões reais, artefatos proprietários ou caches de ferramentas.

A distribuição Codex é determinística e não deve ser editada manualmente:

```powershell
$env:PYTHONUTF8 = "1"
python scripts/generate_codex_plugin.py
python scripts/generate_codex_plugin.py --check
```

O segundo comando falha se faltar um arquivo, existir um arquivo não gerenciado
na árvore de skills, a fonte deixar de conter exatamente 90 descritores ou
houver drift em relação à fonte canônica. Depois da geração, valide as 90 skills
com `quick_validate.py` e o pacote completo com
`validate_plugin.py plugins/pbes`.

No Windows, mantenha `PYTHONUTF8=1` também ao chamar os validadores para que a
leitura das skills não dependa da code page ativa do terminal.
