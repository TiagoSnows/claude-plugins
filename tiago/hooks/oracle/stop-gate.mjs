// Stop / SubagentStop: before the agent ends its turn,
//   1. while tests are locked, checks that no test file changed (hashes vs. the lock snapshot);
//   2. if the project opted in with .claude/check.json, runs the check when the tree changed since the last green run.
// Blocks at most MAX_CONSECUTIVE_BLOCKS times in a row, then lets the agent stop and warns the user.
import path from 'node:path'
import {
  readInput,
  projectOf,
  readState,
  readJson,
  writeJson,
  diffSnapshot,
  readCheckConfig,
  runCheck,
  summarizeFailures,
  worktreeFingerprint,
  isOracleAgent,
  GATED_SUBAGENTS,
  MAX_CONSECUTIVE_BLOCKS,
  CLI,
} from './lib.mjs'

function integrityProblem(project, state) {
  const diff = diffSnapshot(project, state)
  if (diff.clean) return null
  const lines = ['Os testes travados pelo oráculo mudaram desde a trava:']
  if (diff.changed.length) lines.push(`- alterados: ${diff.changed.join(', ')}`)
  if (diff.removed.length) lines.push(`- removidos: ${diff.removed.join(', ')}`)
  if (diff.added.length) lines.push(`- arquivos de teste novos: ${diff.added.join(', ')}`)
  if (diff.config.length) lines.push(`- configuração de teste alterada: ${diff.config.join(', ')}`)
  lines.push(`Restaurar os arquivos travados: ${CLI} restore`)
  lines.push(`Se foi o usuário que mudou os testes de propósito, ele atualiza a trava com: ${CLI} relock`)
  return lines.join('\n')
}

function gateProblem(project, state) {
  const config = readCheckConfig(project)
  if (!config) return null
  const fingerprint = worktreeFingerprint(project)
  if (!fingerprint) return null
  const greenFile = path.join(project.stateDir, 'last-green.json')
  if (readJson(greenFile)?.fingerprint === fingerprint) return null

  const result = runCheck(project, config)
  if (result.ok) {
    writeJson(greenFile, { fingerprint, at: new Date().toISOString() })
    return null
  }
  return `O check do projeto falhou (\`${config.command}\`, saída ${result.code}). Falhas:\n${summarizeFailures(result.output)}`
}

try {
  const input = await readInput()
  const agent = input.agent_type
  if (isOracleAgent(agent)) process.exit(0)

  const project = projectOf(input.cwd ?? process.cwd())
  const state = readState(project)
  const gated = input.hook_event_name === 'Stop' || GATED_SUBAGENTS.includes(agent)

  const problems = []
  if (state?.phase === 'locked') {
    const problem = integrityProblem(project, state)
    if (problem) problems.push(problem)
  }
  if (gated && state?.phase !== 'red') {
    const problem = gateProblem(project, state)
    if (problem) problems.push(problem)
  }

  const counterFile = path.join(project.stateDir, 'stops', `${input.session_id ?? 'session'}-${input.agent_id ?? 'main'}.json`)
  const blocks = input.stop_hook_active ? readJson(counterFile)?.blocks ?? 0 : 0

  if (!problems.length) {
    if (blocks) writeJson(counterFile, { blocks: 0 })
    process.exit(0)
  }
  if (blocks < MAX_CONSECUTIVE_BLOCKS) {
    writeJson(counterFile, { blocks: blocks + 1 })
    process.stdout.write(JSON.stringify({ decision: 'block', reason: problems.join('\n\n') }))
    process.exit(0)
  }
  writeJson(counterFile, { blocks: 0 })
  const summary = problems.map(problem => problem.split('\n')[0]).join(' | ')
  process.stdout.write(
    JSON.stringify({ systemMessage: `Oráculo: o agente encerrou sem resolver depois de ${MAX_CONSECUTIVE_BLOCKS} bloqueios. ${summary}` }),
  )
} catch (error) {
  process.stderr.write(`oracle stop-gate: ${error.message}\n`)
  process.exit(0)
}
