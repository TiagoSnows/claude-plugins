// PreToolUse (Edit|Write|NotebookEdit): enforces who may edit test files during the oracle workflow.
// Phase "red": only the test-oracle subagent writes tests. Phase "locked": nobody edits tests.
// Edits made through Bash/PowerShell are caught by the hash check in stop-gate.mjs.
import path from 'node:path'
import { readInput, projectOf, readState, relativeTo, isTestPath, isOracleAgent, ORACLE_AGENT } from './lib.mjs'

try {
  const input = await readInput()
  const file = input.tool_input?.file_path ?? input.tool_input?.notebook_path
  if (!file) process.exit(0)

  const project = projectOf(path.dirname(path.resolve(file)))
  const state = readState(project)
  if (!state) process.exit(0)

  const rel = relativeTo(project, file)
  if (!rel || !isTestPath(rel)) process.exit(0)
  if (state.phase === 'red' && isOracleAgent(input.agent_type)) process.exit(0)

  const reason =
    state.phase === 'locked'
      ? `Os testes estão travados pelo oráculo (${rel}). A implementação não altera testes. Se um teste parece errado ou a tarefa é impossível como especificada, pare e reporte ao usuário com a evidência.`
      : `Na fase de escrita de testes, só o subagente ${ORACLE_AGENT} escreve testes (${rel}). Delegue a ele ou reporte ao usuário.`

  process.stdout.write(
    JSON.stringify({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason } }),
  )
} catch (error) {
  process.stderr.write(`oracle guard: ${error.message}\n`)
  process.exit(0)
}
