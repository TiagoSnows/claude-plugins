# Arsenal: qual skill citar em cada frente

Consulte ao escolher uma skill para uma frente concreta. Ao instalar uma skill nova, acrescente uma linha aqui.

## Regras

1. **Confira antes de citar.** A skill precisa aparecer na lista de skills disponíveis da sessão. Nunca diga que usou uma que não viu.
2. **Cite no brief.** A subsessão não adivinha: "Carregue a skill `tiago:oraculo` e faça X."
3. **Skill ausente:** avise o usuário na hora dizendo qual skill faltou e o que ela melhoraria, depois siga com bom senso.
4. **Nunca instale por conta própria.** Instalar é decisão do usuário.

## Design

Use a skill `design`, que reúne `impeccable`, `design-taste-frontend`, `redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui`, `industrial-brutalist-ui`, `gpt-taste` e `stitch-design-taste`.

A mestre define o estilo antes de abrir a frente, perguntando ao usuário se a direção visual for decisão dele, e cita no brief: "Carregue a skill `design` e use o estilo `minimalist-ui`." Uma filha não pergunta, porque ficaria parada esperando resposta. Para frentes de interface paralelas no mesmo produto, use o mesmo estilo.

## Processo e qualidade

| Skill | Para quê |
|---|---|
| `tiago:oraculo` | Feature ou bug não trivial em que os testes devem julgar o trabalho. O `tiago:test-oracle` dela fica no Opus, e os hooks do plugin bloqueiam o encerramento da filha até o check passar. |
| `seguranca` | Código que toca input externo, autenticação, arquivos, shell, SQL, rede, segredos ou CI. |
| `code-review` | Revisar um diff ou PR. Útil para conferir a branch de uma subsessão. |
| `security-review` | Revisar a segurança das mudanças pendentes da branch. |
| `simplify` | Limpar o código alterado, sem caçar bugs. |
| `run` | Abrir o app do projeto e ver a mudança funcionando. |

## Pesquisa e arte

| Skill | Para quê |
|---|---|
| `deep-research` | Pesquisa com várias fontes e relatório. Cria subagentes, então rode na mestre ou numa subsessão própria, nunca dentro de um subagente. |
| `tiago:flow-manager` | Gerar arte no Google Flow. |
