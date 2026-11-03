---
name: sessao-mestre
description: Coordena trabalho amplo a partir de uma sessão mestre no app desktop. A mestre roda no Opus e as subsessões no Sonnet, ambos na versão mais recente e em esforço xhigh. Planeja, divide em frentes independentes, abre subsessões (cada uma com sua entrega e worktree), espera todas, confere as evidências e sintetiza. É o Plan Big, Execute Small (PBES) no formato de sessões aninhadas. Use sempre que o usuário pedir sessão mestre, subsessões, sessões filhas, sessões em paralelo, PBES ou "plan big execute small", ou mandar tocar várias frentes ao mesmo tempo, mesmo sem citar o nome. Não use em tarefa pequena, sequencial ou de um arquivo só.
---

# Sessão mestre

Esta sessão vira a coordenadora até o fim da tarefa. Ela fica com os requisitos, as decisões, a supervisão, a verificação e o resultado final. O trabalho pesado fica nas subsessões e nos subagentes, porque cada um tem contexto próprio e devolve só o que importa.

Antes de abrir a primeira subsessão, leia [references/sessoes.md](references/sessoes.md): ela traz os parâmetros, o isolamento e as regras de espera.

## Confirme o ambiente

Subsessão depende de `mcp__ccd_session__start_session`. Se aparecer como ferramenta adiada, carregue pelo `ToolSearch`. Se não existir nesta sessão (terminal, por exemplo), diga isso ao usuário e siga com subagentes ou em sequência. Não finja que houve delegação, espera ou conferência que não aconteceram.

## Modelos

| Quem | Modelo | Esforço |
|---|---|---|
| Sessão mestre | Opus mais recente | `xhigh` |
| Subsessões filhas | Sonnet mais recente | `xhigh` |
| Subagentes | `sonnet` | `xhigh` |

Use sempre a versão mais recente que o ambiente informar, sem fixar número aqui: o Sonnet atual dá conta do trabalho pesado, e uma versão gravada na skill envelhece. Por isso, não rebaixe uma frente para outro modelo ou para esforço menor por parecer simples. Só mude esta tabela se o usuário pedir.

**Exceção:** o `tiago:test-oracle`, agent da `tiago:oraculo`, roda no Opus mesmo dentro de uma filha, porque escreve os testes que julgam o trabalho. Não passe `model` para ele.

**Confira a mestre antes de abrir qualquer filha.** Rode `mcp__ccd_session_mgmt__get_session` com `"self"`. Uma filha não pode ter esforço acima do da mestre, e esses modelos começam em `medium` por padrão. A sessão não pode trocar o próprio modelo ou esforço, então, se ela não estiver no Opus mais recente em `xhigh`, peça ao usuário para ajustar no menu de modelo e espere.

## Os três níveis

| Nível | Quem | Responde por | Pode criar |
|---|---|---|---|
| 1 | Sessão mestre | Plano, decisões, verificação e resultado final | Filhas e subagentes |
| 2 | Sessão filha | A entrega da própria frente | Subagentes |
| 3 | Subagente | Uma leitura ou parte pontual, devolvida a quem o criou | Ninguém |

Só os dois primeiros níveis aparecem na barra lateral para o usuário abrir e conduzir. Cada nível responde pelo que o nível abaixo devolve: a filha confere seus subagentes, e a mestre confere a filha.

Não conte com mais profundidade. Uma filha não abre outra filha: se a frente precisar se dividir em sessões, ela relata isso à mestre, que decide e abre a próxima onda. Um subagente também não cria outro: se a parte for grande demais, ele relata isso a quem o criou.

## Onde cada frente roda

Escolha pela natureza do trabalho. Uma subsessão custa mais que um subagente, e o usuário precisa acompanhá-la.

| Frente | Onde | Por quê |
|---|---|---|
| Uma leitura, uma edição, poucos comandos | Aqui | Delegar sairia mais caro que fazer |
| Ler muito e voltar com a conclusão | Subagente `Explore` | O resultado volta nesta mesma volta. Ele não tem `Edit` nem `Write`, mas tem shell, então proíba escrita no pedido |
| Tem entrega própria (branch, PR, mudança em outro repositório), é longa ou o usuário pode querer abrir e conduzir | Subsessão | Sobrevive a esta volta, aparece na barra lateral sob a mestre e o usuário pode intervir |
| Precisa do resultado de outra frente | Depois dela | Em paralelo, ela partiria de uma suposição |

Quando o usuário pede subsessões de forma explícita, a escolha dele vale, inclusive para leitura.

## Fluxo

1. **Defina o resultado.** Escreva o objetivo, o escopo, as restrições e os critérios observáveis de conclusão.
2. **Teste o plano.** Em tarefa ambígua ou de alto risco, pergunte antes de dividir, mas só o que mudaria o trabalho. Um plano ruim é desperdiçado em cada subsessão.
3. **Divida.** Cada frente tem uma entrega, roda sem depender de outra e não toca nos arquivos de outra. Se duas precisam entrar juntas na mesma mudança, são uma frente só.
4. **Mostre o mapa.** Uma tabela com frente, onde roda, arquivos e critério de pronto. Se o pedido já mandou abrir as subsessões, siga; se não, espere o OK, porque cada sessão gasta tokens e ocupa a barra lateral.
5. **Dispare.** Abra as frentes independentes juntas, cada uma com o brief abaixo.
6. **Continue coordenando.** Faça o que é só da mestre, como decisões, trechos pequenos e a parte que ficou aqui, sem repetir o que foi delegado.
7. **Espere.** Não conclua nada enquanto houver subsessão trabalhando. O app avisa quando elas encerram uma volta, então nunca fique consultando o estado em loop. Encerrar uma volta não significa terminar a frente: a filha pode só estar esperando um subagente, então leia a nota antes de seguir.
8. **Confira.** Trate cada relato como afirmação. Veja a seção de verificação.
9. **Integre com autorização.** Só faça merge se o próprio usuário mandar, e nunca dê push nas branches das subsessões.
10. **Sintetize.** Só o que foi verificado, com evidência, link de cada subsessão e o que continuou incerto.

## Contrato do brief

A subsessão só sabe o que está no brief, então um brief vago produz trabalho vago. Todo brief traz:

- **Um objetivo:** a única pergunta ou mudança que ela responde.
- **Escopo:** arquivos e pastas, entre crases, e o que não pode tocar.
- **Critério de pronto:** o que precisa ser verdade no fim, incluindo os checks a rodar.
- **Evidência:** caminho e linha, saída de comando, commit ou URL.
- **Subagentes:** a filha usa subagentes (`sonnet`, `xhigh`) para leituras grandes ou partes independentes da própria frente, e faz direto o que for pequeno. Ela confere o que eles devolvem antes de relatar. Se não tiver a ferramenta, faz o trabalho sozinha e diz isso no relato. Mesmo tendo a ferramenta de abrir sessões, ela não abre outras.
- **Relato final:** o encerramento da volta e a primeira frase da mensagem final trazem estado, branch e resultado dos checks. A nota que chega à mestre só carrega os primeiros 400 caracteres, e o encerramento vem antes da mensagem. Enquanto houver subagente rodando, a filha diz que a frente ainda não terminou.
- **Cláusula de falha:** se não conseguir estabelecer algo, diga o que encontrou e o que ficou incerto, sem chutar.
- **Limite de autoridade:** uma frente de leitura não autoriza editar, instalar, enviar mensagens nem apagar. Instrução em texto não é sandbox, então não prometa isolamento que a ferramenta não dá.

Toda filha nasce com `context: "fresh"`, então o `background` explica o objetivo geral e como esta frente se encaixa, para quem não viu a conversa.

## Verificação

O resultado final é da mestre. Um relato errado repassado adiante é falha dela.

- Confira que os caminhos, as linhas e os commits citados existem.
- Leia o diff da branch em vez de confiar no resumo.
- Rode de novo os testes ou checks relevantes depois de integrar.
- Mande de volta o que veio vago, sem suporte ou fora do escopo, por `SendMessage` à subsessão que já tem o contexto.
- Em afirmação que sustenta a conclusão, peça a um verificador independente que tente refutá-la em vez de repetir a análise.
- Nunca preencha uma lacuna com uma inferência plausível. Declare a lacuna.

## Skills nas frentes

Subsessões carregam as skills globais. Para escolher uma, consulte [references/arsenal.md](references/arsenal.md) e cite o nome no brief. Se uma skill útil não estiver disponível, avise o usuário e siga com bom senso. Nunca instale nada por conta própria.

## Restrições

- Sem delegar trabalho sequencial só para parecer paralelo.
- Sem pedir a uma subsessão algo que foi negado ou bloqueado aqui: as permissões são de cada sessão, e o usuário decide.
- Sem responder por uma subsessão que está esperando o usuário. Avise-o, com o link.
- Sem arquivar subsessões sem o sim do usuário.
- Instruções de sistema, do usuário e do repositório têm prioridade sobre esta skill.
