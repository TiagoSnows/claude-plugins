// Tests for the fingerprint the stop-gate compares with last-green.json to skip a check that is already green. Run: node --test
// Outside git there is no status or diff to hash, so the fingerprint has to follow the project's files themselves.
import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { worktreeFingerprint } from './lib.mjs'

const roots = []

function tmp() {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'oracle-fingerprint-')))
  roots.push(dir)
  return dir
}

after(() => {
  for (const dir of roots) fs.rmSync(dir, { recursive: true, force: true })
})

function write(root, rel, content = '') {
  const file = path.join(root, rel)
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, content)
}

// A project outside git with a few files and a check, the way the gate finds it.
function plainProject() {
  const root = tmp()
  write(root, 'src/app.js', 'export const answer = 42\n')
  write(root, 'README.md', '# Projeto A\n')
  write(root, '.claude/check.json', JSON.stringify({ command: 'node --version' }))
  return { root, stateDir: path.join(root, '.claude', 'oracle'), isGit: false }
}

describe('worktreeFingerprint outside git', () => {
  it('is a hash that stays the same while nothing changes', () => {
    const project = plainProject()
    const first = worktreeFingerprint(project)
    assert.match(first, /^[0-9a-f]{64}$/)
    assert.equal(worktreeFingerprint(project), first)
  })

  it('changes when a file is edited', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, 'src/app.js', 'export const answer = 4242\n')
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('changes when a file is edited without changing its size', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    const file = path.join(project.root, 'src', 'app.js')
    fs.writeFileSync(file, 'export const answer = 43\n')
    const later = new Date(Date.now() + 60_000)
    fs.utimesSync(file, later, later)
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('changes when a file is created', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, 'src/extra.js', 'export {}\n')
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('changes when a file is removed', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    fs.rmSync(path.join(project.root, 'README.md'))
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('changes when .claude/check.json changes, so a new command runs again', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, '.claude/check.json', JSON.stringify({ command: 'node --test' }))
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('is not changed by the oracle writing its own state, last-green.json included', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, '.claude/oracle/last-green.json', JSON.stringify({ fingerprint: before, at: '2026-01-01T00:00:00Z' }))
    write(project.root, '.claude/oracle/state.json', JSON.stringify({ phase: 'locked' }))
    write(project.root, '.claude/oracle/snapshot/tests/app.test.js', 'copy of a locked test\n')
    write(project.root, '.claude/oracle/stops/s1-main.json', JSON.stringify({ blocks: 1 }))
    assert.equal(worktreeFingerprint(project), before)
    write(project.root, '.claude/oracle/last-green.json', JSON.stringify({ fingerprint: before, at: '2026-01-02T00:00:00Z', again: true }))
    assert.equal(worktreeFingerprint(project), before)
  })

  it('is not changed by linked worktrees kept under .claude/worktrees', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, '.claude/worktrees/feature/src/app.js', 'export const answer = 0\n')
    assert.equal(worktreeFingerprint(project), before)
  })

  it('is not changed by dependency and build folders', () => {
    const project = plainProject()
    const before = worktreeFingerprint(project)
    write(project.root, 'node_modules/lib/index.js', 'module.exports = 1\n')
    write(project.root, 'dist/app.js', 'bundle\n')
    write(project.root, 'sub/__pycache__/mod.pyc', 'bytecode\n')
    assert.equal(worktreeFingerprint(project), before)
  })

  it('is not changed by a nested repository, which is another project', () => {
    const project = plainProject()
    write(project.root, 'vendor/other/.git/HEAD', 'ref: refs/heads/main\n')
    write(project.root, 'vendor/other/index.js', 'export {}\n')
    const before = worktreeFingerprint(project)
    write(project.root, 'vendor/other/index.js', 'export const changed = true\n')
    write(project.root, 'vendor/other/new.js', 'export {}\n')
    assert.equal(worktreeFingerprint(project), before)
  })

  it('does not take a .git leftover without HEAD for a nested repository', () => {
    const project = plainProject()
    write(project.root, 'tools/.git/info/exclude', '')
    write(project.root, 'tools/run.js', 'export {}\n')
    const before = worktreeFingerprint(project)
    write(project.root, 'tools/run.js', 'export const changed = true\n')
    assert.notEqual(worktreeFingerprint(project), before)
  })

  it('is null when the project has no files besides the oracle state', () => {
    const root = tmp()
    write(root, '.claude/oracle/state.json', JSON.stringify({ phase: 'locked' }))
    assert.equal(worktreeFingerprint({ root, stateDir: path.join(root, '.claude', 'oracle'), isGit: false }), null)
  })
})

describe('stop-gate in a project without git', () => {
  const gate = fileURLToPath(new URL('./stop-gate.mjs', import.meta.url))

  it('runs the check again after a change instead of only the first time', () => {
    const project = plainProject()
    // The counter lives outside the project: a file the check wrote inside it would count as a change.
    const counter = path.join(tmp(), 'runs.txt')
    const command = `node -e "require('fs').appendFileSync(process.env.ORACLE_CHECK_RUNS, 'x')"`
    write(project.root, '.claude/check.json', JSON.stringify({ command }))
    const runs = () => (fs.existsSync(counter) ? fs.readFileSync(counter, 'utf8').length : 0)
    const stop = () => {
      const input = JSON.stringify({ hook_event_name: 'Stop', cwd: project.root, session_id: 's1' })
      const result = spawnSync(process.execPath, [gate], { input, encoding: 'utf8', env: { ...process.env, ORACLE_CHECK_RUNS: counter } })
      assert.equal(result.status, 0, result.stderr)
      assert.equal(result.stdout, '', result.stdout)
      return runs()
    }

    assert.equal(stop(), 1, 'the first stop runs the check')
    assert.equal(stop(), 1, 'a second stop with nothing changed skips it')
    write(project.root, 'src/app.js', 'export const answer = 4242\n')
    assert.equal(stop(), 2, 'a stop after editing a file runs it again')
    assert.equal(stop(), 2, 'and the new green run is sealed too')
  })
})
