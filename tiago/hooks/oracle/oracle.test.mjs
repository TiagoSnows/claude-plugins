// Tests for project resolution (lib.mjs) and for how the CLI and the hooks use it. Run: node --test
// Everything happens in temporary folders; nothing outside them is read or written.
import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { projectOf, listTestFiles, sha256 } from './lib.mjs'

const script = name => fileURLToPath(new URL(name, import.meta.url))
const roots = []

function tmp() {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'oracle-test-')))
  roots.push(dir)
  return dir
}

after(() => {
  for (const dir of roots) fs.rmSync(dir, { recursive: true, force: true })
})

function write(file, content = '') {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, content)
  return file
}

// A leftover .git that is not a repository: only info/ and claude-oracle/, as left behind in a folder that groups several projects.
function leftoverGit(dir) {
  fs.mkdirSync(path.join(dir, '.git', 'info'), { recursive: true })
  fs.mkdirSync(path.join(dir, '.git', 'claude-oracle'), { recursive: true })
}

// A minimal valid .git directory, without needing the git binary.
function minimalGit(dir) {
  write(path.join(dir, '.git', 'HEAD'), 'ref: refs/heads/main\n')
  fs.mkdirSync(path.join(dir, '.git', 'refs'), { recursive: true })
}

const author = { GIT_AUTHOR_NAME: 'teste', GIT_AUTHOR_EMAIL: 'teste@example.com', GIT_COMMITTER_NAME: 'teste', GIT_COMMITTER_EMAIL: 'teste@example.com' }

function git(cwd, ...args) {
  const result = spawnSync('git', ['-c', 'commit.gpgsign=false', ...args], { cwd, encoding: 'utf8', env: { ...process.env, ...author } })
  assert.equal(result.status, 0, `git ${args.join(' ')}: ${result.stderr}`)
  return result.stdout
}

function initRepo(dir) {
  fs.mkdirSync(dir, { recursive: true })
  git(dir, 'init', '-q')
  git(dir, 'commit', '-q', '--allow-empty', '-m', 'init')
  return dir
}

const cli = (cwd, ...args) => spawnSync(process.execPath, [script('./oracle.mjs'), ...args], { cwd, encoding: 'utf8' })
const hook = (name, input) => spawnSync(process.execPath, [script(`./${name}.mjs`)], { input: JSON.stringify(input), encoding: 'utf8' })
const stopGate = cwd => hook('stop-gate', { hook_event_name: 'Stop', cwd, session_id: 's1' })

// Two sibling projects without git under a parent that has a leftover .git.
function siblings() {
  const parent = tmp()
  leftoverGit(parent)
  const a = path.join(parent, 'Projeto A')
  const b = path.join(parent, 'Projeto B')
  write(path.join(a, 'tests', 'a.test.js'), 'a')
  write(path.join(b, 'tests', 'b.test.js'), 'b')
  return { parent, a, b }
}

describe('projectOf', () => {
  it('ignores a leftover .git in a parent folder and uses the project folder', () => {
    const { parent, a } = siblings()
    const project = projectOf(a)
    assert.equal(project.root, a)
    assert.equal(project.isGit, false)
    assert.equal(project.stateDir, path.join(a, '.claude', 'oracle'))
    assert.deepEqual(fs.readdirSync(path.join(parent, '.git', 'claude-oracle')), [])
  })

  it('stops at the first folder that holds a lock when started from a subfolder', () => {
    const { a } = siblings()
    write(path.join(a, '.claude', 'oracle', 'state.json'), '{}')
    const deep = path.join(a, 'src', 'deep')
    fs.mkdirSync(deep, { recursive: true })
    assert.equal(projectOf(deep).root, a)
  })

  it('never adopts a parent folder that has no lock', () => {
    const parent = tmp()
    write(path.join(parent, '.claude', 'oracle', 'last-green.json'), '{}')
    const sub = path.join(parent, 'app', 'src')
    fs.mkdirSync(sub, { recursive: true })
    assert.equal(projectOf(sub).root, sub)
  })

  it('uses the toplevel of a valid repository from any subfolder', () => {
    const repo = initRepo(path.join(tmp(), 'repo'))
    const deep = path.join(repo, 'a', 'b')
    fs.mkdirSync(deep, { recursive: true })
    const project = projectOf(deep)
    assert.equal(project.root, repo)
    assert.equal(project.isGit, true)
    assert.equal(project.stateDir, path.join(repo, '.git', 'claude-oracle'))
  })

  it('does not stop at a stray .git inside a valid repository', () => {
    const repo = initRepo(path.join(tmp(), 'repo'))
    leftoverGit(path.join(repo, 'vendor'))
    assert.equal(projectOf(path.join(repo, 'vendor')).root, repo)
  })

  it('accepts a .git directory only with HEAD and objects/ or refs/', () => {
    const cases = [
      { name: 'HEAD + refs', files: ['HEAD'], dirs: ['refs'], valid: true },
      { name: 'HEAD + objects', files: ['HEAD'], dirs: ['objects'], valid: true },
      { name: 'only HEAD', files: ['HEAD'], dirs: [], valid: false },
      { name: 'objects + refs without HEAD', files: [], dirs: ['objects', 'refs'], valid: false },
      { name: 'only info and claude-oracle', files: [], dirs: ['info', 'claude-oracle'], valid: false },
    ]
    for (const { name, files, dirs, valid } of cases) {
      const parent = tmp()
      for (const file of files) write(path.join(parent, '.git', file), 'ref: refs/heads/main\n')
      for (const dir of dirs) fs.mkdirSync(path.join(parent, '.git', dir), { recursive: true })
      const child = path.join(parent, 'child')
      fs.mkdirSync(child)
      assert.equal(projectOf(child).root, valid ? parent : child, name)
    }
  })

  it('treats a linked worktree as its own project', () => {
    const base = tmp()
    const repo = initRepo(path.join(base, 'repo'))
    const worktree = path.join(base, 'wt')
    git(repo, 'worktree', 'add', '-q', '--detach', worktree)
    const sub = path.join(worktree, 'src')
    fs.mkdirSync(sub)
    const project = projectOf(sub)
    assert.equal(project.root, worktree)
    assert.equal(project.isGit, true)
    assert.match(path.dirname(project.stateDir), /[\\/]worktrees[\\/]wt$/)
    assert.ok(fs.statSync(path.dirname(project.stateDir)).isDirectory())
    assert.equal(projectOf(repo).root, repo)
  })

  it('rejects a .git file whose gitdir does not exist or is missing', () => {
    const parent = tmp()
    write(path.join(parent, 'broken', '.git'), 'gitdir: ../nowhere\n')
    write(path.join(parent, 'garbage', '.git'), 'not a pointer\n')
    for (const name of ['broken', 'garbage']) {
      const sub = path.join(parent, name, 'src')
      fs.mkdirSync(sub, { recursive: true })
      assert.equal(projectOf(sub).root, sub, name)
    }
  })

  it('accepts a .git file whose gitdir exists', () => {
    const base = tmp()
    fs.mkdirSync(path.join(base, 'store'))
    write(path.join(base, 'linked', '.git'), 'gitdir: ../store\n')
    const project = projectOf(path.join(base, 'linked'))
    assert.equal(project.root, path.join(base, 'linked'))
    assert.equal(project.stateDir, path.join(base, 'store', 'claude-oracle'))
  })
})

describe('listTestFiles', () => {
  it('skips nested repositories, .claude/worktrees, the oracle snapshot, and dependency folders when there is no git', () => {
    const root = tmp()
    write(path.join(root, 'tests', 'ok.test.js'))
    write(path.join(root, '.claude', 'oracle', 'snapshot', 'tests', 'ok.test.js'))
    write(path.join(root, 'legacy', 'tests', 'old.test.js'))
    leftoverGit(path.join(root, 'legacy'))
    minimalGit(path.join(root, 'packages', 'lib'))
    write(path.join(root, 'packages', 'lib', 'tests', 'inner.test.js'))
    write(path.join(root, '.claude', 'worktrees', 'w1', 'tests', 'w1.test.js'))
    write(path.join(root, '.claude', 'worktrees', 'w2', '.git'), `gitdir: ${root}\n`)
    write(path.join(root, '.claude', 'worktrees', 'w2', 'tests', 'w2.test.js'))
    write(path.join(root, 'node_modules', 'pkg', 'tests', 'n.test.js'))
    const project = projectOf(root)
    assert.equal(project.isGit, false)
    assert.deepEqual(listTestFiles(project).sort(), ['legacy/tests/old.test.js', 'tests/ok.test.js'])
  })

  it('skips nested repositories and .claude/worktrees when git lists the files', () => {
    const repo = initRepo(path.join(tmp(), 'repo'))
    write(path.join(repo, 'tests', 'a.test.js'))
    write(path.join(repo, '.claude', 'worktrees', 'w', 'tests', 'x.test.js'))
    initRepo(path.join(repo, 'test', 'inner'))
    write(path.join(repo, 'test', 'inner', 't.test.js'))
    const project = projectOf(repo)
    assert.equal(project.isGit, true)
    assert.deepEqual(listTestFiles(project), ['tests/a.test.js'])
  })
})

describe('oracle CLI', () => {
  it('status shows the project folder, from cwd or --dir, when a parent has a leftover .git', () => {
    const { parent, a } = siblings()
    const projectLine = result => result.stdout.split(/\r?\n/).find(line => line.startsWith('Projeto: '))
    assert.equal(projectLine(cli(a, 'status')), `Projeto: ${a}`)
    assert.equal(projectLine(cli(os.tmpdir(), 'status', '--dir', a)), `Projeto: ${a}`)
    assert.notEqual(projectLine(cli(parent, 'status')), `Projeto: ${a}`)
  })

  it('lock keeps the state and the snapshot inside the project and ignores sibling projects', () => {
    const { parent, a } = siblings()
    const result = cli(a, 'lock')
    assert.equal(result.status, 0, result.stderr)
    const state = JSON.parse(fs.readFileSync(path.join(a, '.claude', 'oracle', 'state.json'), 'utf8'))
    assert.deepEqual(Object.keys(state.files), ['tests/a.test.js'])
    assert.deepEqual(fs.readdirSync(path.join(parent, '.git', 'claude-oracle')), [])
  })

  it('init-check writes check.json in the project, not in a parent folder', () => {
    const { parent, a } = siblings()
    assert.equal(cli(a, 'init-check', 'echo ok').status, 0)
    assert.ok(fs.existsSync(path.join(a, '.claude', 'check.json')))
    assert.ok(!fs.existsSync(path.join(parent, '.claude', 'check.json')))
  })
})

describe('hooks', () => {
  it('stop-gate stays quiet right after lock in a project without git', () => {
    const project = tmp()
    write(path.join(project, 'tests', 'a.test.js'), 'a')
    assert.equal(cli(project, 'lock').status, 0)
    assert.ok(fs.existsSync(path.join(project, '.claude', 'oracle', 'snapshot', 'tests', 'a.test.js')))
    assert.equal(stopGate(project).stdout, '')
  })

  it('stop-gate does not block for a test changed in another project', () => {
    const { a, b } = siblings()
    assert.equal(cli(a, 'lock').status, 0)
    write(path.join(b, 'tests', 'b.test.js'), 'changed')
    write(path.join(b, 'tests', 'novo.test.js'), 'new')
    const result = stopGate(a)
    assert.equal(result.status, 0, result.stderr)
    assert.equal(result.stdout, '')
  })

  it('stop-gate still blocks for a test changed in its own project', () => {
    const { a } = siblings()
    assert.equal(cli(a, 'lock').status, 0)
    write(path.join(a, 'tests', 'a.test.js'), 'changed')
    const result = stopGate(a)
    assert.equal(JSON.parse(result.stdout).decision, 'block')
    assert.match(JSON.parse(result.stdout).reason, /tests\/a\.test\.js/)
  })

  it('a stale lock in the leftover .git of a parent folder affects no project', () => {
    const { parent, a, b } = siblings()
    const stale = { phase: 'locked', lockedAt: new Date().toISOString(), files: { 'Projeto B/tests/b.test.js': sha256('antigo') }, embedded: {} }
    write(path.join(parent, '.git', 'claude-oracle', 'state.json'), JSON.stringify(stale))
    assert.equal(stopGate(a).stdout, '')
    const edit = file => hook('guard', { tool_name: 'Write', tool_input: { file_path: file, content: 'x' } })
    assert.equal(edit(path.join(a, 'tests', 'novo.test.js')).stdout, '')
    assert.equal(edit(path.join(b, 'tests', 'b.test.js')).stdout, '')
  })

  it('guard denies test edits only in the locked project, including paths that do not exist yet', () => {
    const { a, b } = siblings()
    assert.equal(cli(a, 'lock').status, 0)
    const edit = file => hook('guard', { tool_name: 'Write', tool_input: { file_path: file, content: 'x' } })
    const denied = JSON.parse(edit(path.join(a, 'src', 'deep', 'tests', 'novo.test.js')).stdout)
    assert.equal(denied.hookSpecificOutput.permissionDecision, 'deny')
    assert.match(denied.hookSpecificOutput.permissionDecisionReason, /\(src\/deep\/tests\/novo\.test\.js\)/)
    assert.equal(edit(path.join(b, 'tests', 'novo.test.js')).stdout, '')
  })

  it('detector reports paths relative to the project folder while a flow is active', () => {
    const { a } = siblings()
    assert.equal(cli(a, 'red').status, 0)
    const input = { tool_name: 'Write', tool_input: { file_path: path.join(a, 'tests', 'x.test.js'), content: 'it.skip("x", () => {})' } }
    const context = JSON.parse(hook('detector', input).stdout).hookSpecificOutput.additionalContext
    assert.ok(context.includes('A edição em tests/x.test.js introduziu'), context)
  })
})
