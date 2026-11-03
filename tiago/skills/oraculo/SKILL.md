---
name: oraculo
description: Fluxo de TDD com oráculo independente. Um subagente (test-oracle) escreve os testes de aceite ou de reprodução a partir da spec, o usuário aprova as asserções, os testes ficam travados por hook e a implementação segue até o check do projeto ficar verde. Use em feature ou correção de bug não trivial em que os testes devem julgar o trabalho, ou quando o usuário pedir /oraculo. Não use para mudanças que cabem numa frase.
---

# Oráculo de testes

Quem implementa não escreve os testes que julgam o próprio trabalho. Testes gerados depois do código, no mesmo contexto, herdam os bugs dele. Testes escritos da spec em contexto separado e aprovados pelo usuário são o oráculo.

CLI do fluxo (rode no diretório do projeto): `node "${CLAUDE_PLUGIN_ROOT}/hooks/oracle/oracle.mjs" <comando>`
Comandos: `status`, `red`, `lock`, `relock`, `unlock`, `restore`, `check`, `init-check "<comando>"`.

## 1. Critérios de aceite

- Bug: o relato do bug (o que acontece, o que deveria acontecer, como reproduzir) é a spec.
- Feature: a spec precisa terminar em critérios verificáveis (entrada → resultado esperado). Se faltarem, proponha os critérios ao usuário e confirme antes de seguir.
- Se o diff cabe numa frase, não use este fluxo: faça a mudança e rode os checks existentes.

## 2. Check do projeto

- Rode `status`. Se não houver check configurado, descubra o comando que roda testes, tipos e lint do projeto (scripts do package.json, pyproject, Makefile) e mostre ao usuário.
- Com o OK do usuário, grave: `init-check "<comando>"` (opções `--shell bash|powershell|cmd`, `--timeout <seg>`). A partir daí, um hook roda esse check antes de o agente encerrar e só deixa encerrar com verde.

## 3. Testes pelo oráculo

- Rode `red`. Nessa fase só o subagente `tiago:test-oracle` pode editar arquivos de teste.
- Delegue ao `tiago:test-oracle` (Agent tool, `subagent_type: "tiago:test-oracle"`) passando:
  - os critérios de aceite ou o relato do bug, literalmente;
  - os caminhos úteis para chamar o código (API pública, fixtures, testes vizinhos);
  - o comando de teste.
- Não passe o plano de implementação além das interfaces.
- Confira no relatório que os testes falham pelo motivo certo, não por erro de import ou sintaxe.

## 4. Aprovação

Mostre ao usuário a tabela critério → teste → valor esperado (com a origem de cada valor). Para ajustar, peça ao oráculo e mostre de novo. Não siga sem a aprovação.

## 5. Trava

Rode `lock`. A partir daqui nenhum agente edita testes. O hook nega edições, e um hash detecta mudanças feitas por qualquer outro caminho antes de o agente encerrar.

## 6. Implementação

- Implemente em incrementos pequenos, rodando os testes travados.
- Não altere, pule nem contorne testes.
- Se um teste parecer errado ou a tarefa for impossível como especificada, pare e reporte ao usuário com a evidência. Se ele concordar: `unlock`, o oráculo corrige o teste, nova aprovação, `lock`.
- Se a mesma correção falhar duas vezes, pare de empilhar tentativas: resuma o que aprendeu e reformule ou consulte o usuário.

## 7. Fim

- Pronto = check verde depois da última mudança. Reporte o comando e o resultado.
- Com o usuário satisfeito, rode `unlock` para encerrar o fluxo.
