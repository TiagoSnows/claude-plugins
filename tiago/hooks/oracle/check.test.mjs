// Tests for how runCheck picks the shell of .claude/check.json. Run: node --test
// On Windows a bare `bash` resolves to the WSL launcher in System32, which fails with "execvpe(/bin/bash) failed".
import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { runCheck } from './lib.mjs'

const roots = []

function tmp() {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'oracle-check-')))
  roots.push(dir)
  return dir
}

after(() => {
  for (const dir of roots) fs.rmSync(dir, { recursive: true, force: true })
})

const gitBash = ['ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)']
  .flatMap(name => (process.env[name] ? [path.join(process.env[name], 'Git', 'usr', 'bin', 'bash.exe')] : []))
  .find(file => fs.existsSync(file))
const windowsOnly = { skip: process.platform !== 'win32' ? 'Windows only' : !gitBash && 'Git Bash not installed' }

// PATH with System32 first, where the WSL launcher lives, whatever the machine's own order is.
const system32First = () => `${path.join(process.env.SystemRoot ?? 'C:\\Windows', 'System32')}${path.delimiter}${process.env.PATH ?? ''}`

function withEnv(vars, run) {
  const saved = Object.fromEntries(Object.keys(vars).map(name => [name, process.env[name]]))
  Object.assign(process.env, vars)
  try {
    return run()
  } finally {
    for (const [name, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[name]
      else process.env[name] = value
    }
  }
}

const withPath = (PATH, run) => withEnv({ PATH }, run)

// Only a real bash expands these; cmd.exe would print them literally, and WSL's bash would say GNU/Linux instead of Msys.
const GIT_BASH_ONLY = 'echo "$BASH_VERSINFO $(uname -o)"'
const GIT_BASH_OUTPUT = /^\d+ Msys$/

describe('runCheck with the bash shell on Windows', windowsOnly, () => {
  it('runs in Git Bash even when the WSL launcher comes first in PATH', () => {
    const result = withPath(system32First(), () => runCheck({ root: tmp() }, { command: GIT_BASH_ONLY, shell: 'bash' }))
    assert.equal(result.ok, true, result.output)
    assert.match(result.output.trim(), GIT_BASH_OUTPUT)
  })

  it('runs the command in the project folder', () => {
    const root = tmp()
    const result = withPath(system32First(), () => runCheck({ root }, { command: 'pwd', shell: 'bash' }))
    assert.equal(result.ok, true, result.output)
    assert.ok(result.output.trim().endsWith(`/${path.basename(root)}`), result.output)
  })

  it('reports the exit code of the command', () => {
    const result = withPath(system32First(), () => runCheck({ root: tmp() }, { command: 'exit 3', shell: 'bash' }))
    assert.equal(result.ok, false)
    assert.equal(result.code, 3)
  })

  it('accepts the full path of a bash executable as the shell', () => {
    const result = withPath(system32First(), () => runCheck({ root: tmp() }, { command: GIT_BASH_ONLY, shell: gitBash }))
    assert.equal(result.ok, true, result.output)
    assert.match(result.output.trim(), GIT_BASH_OUTPUT)
  })

  it('says how to fix it when Git Bash cannot be found', () => {
    const noGit = { ProgramFiles: '', ProgramW6432: '', 'ProgramFiles(x86)': '', LOCALAPPDATA: '', PATH: path.join(process.env.SystemRoot ?? 'C:\\Windows', 'System32') }
    const result = withEnv(noGit, () => runCheck({ root: tmp() }, { command: 'echo ok', shell: 'bash' }))
    assert.equal(result.ok, false)
    assert.equal(result.code, null)
    assert.match(result.output, /Git Bash não encontrado/)
    assert.match(result.output, /check\.json/)
  })

  it('fails with the spawn error when the shell path does not exist', () => {
    const missing = path.join(tmp(), 'no-such-dir', 'bash.exe')
    const result = runCheck({ root: tmp() }, { command: 'echo ok', shell: missing })
    assert.equal(result.ok, false)
    assert.match(result.output, /ENOENT/)
  })

  it('passes through stop-gate with the same PATH a hook gets', () => {
    const project = tmp()
    fs.mkdirSync(path.join(project, '.claude'))
    fs.writeFileSync(path.join(project, '.claude', 'check.json'), JSON.stringify({ command: '[ "$(uname -o)" = Msys ]', shell: 'bash' }))
    const input = JSON.stringify({ hook_event_name: 'Stop', cwd: project, session_id: 's1' })
    const gate = fileURLToPath(new URL('./stop-gate.mjs', import.meta.url))
    const result = spawnSync(process.execPath, [gate], { input, encoding: 'utf8', env: { ...process.env, PATH: system32First() } })
    assert.equal(result.status, 0, result.stderr)
    assert.equal(result.stdout, '', result.stdout)
  })
})

describe('runCheck with the default shell', () => {
  it('still runs the command through the system shell', () => {
    const result = runCheck({ root: tmp() }, { command: 'echo ok' })
    assert.equal(result.ok, true, result.output)
    assert.equal(result.output.trim(), 'ok')
  })
})
