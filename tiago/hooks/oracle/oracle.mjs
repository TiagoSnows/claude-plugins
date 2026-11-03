// CLI for the oracle workflow. Run from the project directory (or pass --dir <path>).
//   status | red | lock | relock | unlock | restore | check | init-check "<command>" [--shell bash|powershell|cmd] [--timeout <sec>]
//   red, lock, and init-check also take --force, to start in a folder that looks like it only groups projects.
import fs from 'node:fs'
import path from 'node:path'
import {
  projectOf,
  startProjectOf,
  readState,
  writeState,
  clearState,
  takeSnapshot,
  diffSnapshot,
  snapshotDir,
  readCheckConfig,
  runCheck,
  summarizeFailures,
  writeJson,
} from './lib.mjs'

const args = process.argv.slice(2)
const option = name => {
  const i = args.indexOf(name)
  return i >= 0 ? args.splice(i, 2)[1] : undefined
}
const flag = name => {
  const i = args.indexOf(name)
  if (i >= 0) args.splice(i, 1)
  return i >= 0
}
const dir = option('--dir') ?? process.cwd()
const shell = option('--shell')
const timeout = option('--timeout')
const force = flag('--force')
const [command, ...rest] = args
// Commands that start a flow never adopt a parent folder; the others find the flow they continue by walking up.
const start = ['red', 'lock', 'init-check'].includes(command) ? startProjectOf(dir, { force }) : null
if (start?.error) {
  console.log(start.error)
  process.exit(1)
}
const project = start?.project ?? projectOf(dir)

function lock() {
  const { files, embedded } = takeSnapshot(project)
  writeState(project, { phase: 'locked', lockedAt: new Date().toISOString(), files, embedded })
  const names = Object.keys(files)
  console.log(`Travados ${names.length} arquivo(s) de teste em ${project.root}`)
  for (const name of names.slice(0, 30)) console.log(`  ${name}`)
  if (names.length > 30) console.log(`  ... e mais ${names.length - 30}`)
}

switch (command) {
  case 'status': {
    const state = readState(project)
    const config = readCheckConfig(project)
    console.log(`Projeto: ${project.root}`)
    console.log(`Fase: ${state?.phase ?? 'nenhuma (sem fluxo de oráculo ativo)'}`)
    if (state?.phase === 'locked') {
      const diff = diffSnapshot(project, state)
      console.log(`Arquivos travados: ${Object.keys(state.files).length} | integridade: ${diff.clean ? 'ok' : 'ALTERADA'}`)
    }
    console.log(`Check: ${config ? config.command : 'não configurado (.claude/check.json)'}`)
    break
  }
  case 'red':
    writeState(project, { phase: 'red', since: new Date().toISOString() })
    console.log('Fase "red": só o subagente test-oracle escreve testes; o gate não exige verde.')
    break
  case 'lock':
  case 'relock':
    lock()
    break
  case 'unlock':
    clearState(project)
    console.log('Trava removida; fluxo de oráculo encerrado.')
    break
  case 'restore': {
    const state = readState(project)
    if (state?.phase !== 'locked') {
      console.log('Nada a restaurar: os testes não estão travados.')
      break
    }
    const diff = diffSnapshot(project, state)
    for (const rel of [...diff.changed, ...diff.removed]) {
      const target = path.join(project.root, rel)
      fs.mkdirSync(path.dirname(target), { recursive: true })
      fs.copyFileSync(path.join(snapshotDir(project), rel), target)
      console.log(`restaurado: ${rel}`)
    }
    if (diff.added.length) console.log(`Arquivos de teste novos (não removidos automaticamente): ${diff.added.join(', ')}`)
    if (diff.config.length) console.log(`Configuração de teste alterada (revise à mão): ${diff.config.join(', ')}`)
    break
  }
  case 'check': {
    const config = readCheckConfig(project)
    if (!config) {
      console.log('Sem .claude/check.json neste projeto.')
      process.exit(1)
    }
    const result = runCheck(project, config)
    console.log(result.ok ? `Check verde: ${config.command}` : `Check falhou (saída ${result.code}):\n${summarizeFailures(result.output)}`)
    process.exit(result.ok ? 0 : 1)
  }
  case 'init-check': {
    const checkCommand = rest.join(' ')
    if (!checkCommand) {
      console.log('Uso: init-check "<comando>" [--shell bash|powershell|cmd] [--timeout <seg>]')
      process.exit(1)
    }
    const config = { command: checkCommand, ...(shell && { shell }), ...(timeout && { timeoutSec: Number(timeout) }) }
    writeJson(path.join(project.root, '.claude', 'check.json'), config)
    console.log(`Gravado ${path.join(project.root, '.claude', 'check.json')}: ${JSON.stringify(config)}`)
    break
  }
  default:
    console.log('Comandos: status | red | lock | relock | unlock | restore | check | init-check "<comando>"')
    process.exit(command ? 1 : 0)
}
