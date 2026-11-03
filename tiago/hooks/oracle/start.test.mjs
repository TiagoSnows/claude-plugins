// Tests for where a flow starts (red, lock, init-check) and how the other commands find it. Run: node --test
import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { worktreeFingerprint } from './lib.mjs'

const CLI = fileURLToPath(new URL('./oracle.mjs', import.meta.url))
const roots = []

function tmp() {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'oracle-start-')))
  roots.push(dir)
  return dir
}

after(() => {
  for (const dir of roots) fs.rmSync(dir, { recursive: true, force: true })
})

function write(file, content = '') {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, content)
}

// A minimal valid .git directory, without needing the git binary.
function minimalGit(dir) {
  write(path.join(dir, '.git', 'HEAD'), 'ref: refs/heads/main\n')
  fs.mkdirSync(path.join(dir, '.git', 'refs'), { recursive: true })
}

const cli = (cwd, ...args) => spawnSync(process.execPath, [CLI, ...args], { cwd, encoding: 'utf8' })
const stateOf = dir => {
  try {
    return JSON.parse(fs.readFileSync(path.join(dir, '.claude', 'oracle', 'state.json'), 'utf8'))
  } catch {
    return null
  }
}
const projectLine = result => result.stdout.split(/\r?\n/).find(line => line.startsWith('Projeto: '))

// A folder that only groups projects: loose notes and a stray lockfile, but no project file, and subfolders that are projects.
function workspace() {
  const root = tmp()
  write(path.join(root, 'notas.md'), 'x')
  write(path.join(root, 'package-lock.json'), '{}')
  write(path.join(root, 'Projeto A', 'README.md'), 'a')
  write(path.join(root, 'Projeto A', 'tests', 'a.test.js'), 'a')
  minimalGit(path.join(root, 'Projeto B'))
  write(path.join(root, 'Projeto B', 'tests', 'b.test.js'), 'b')
  write(path.join(root, 'Projeto C', 'package.json'), '{}')
  write(path.join(root, 'Projeto C', 'tests', 'c.test.js'), 'c')
  return root
}

// A project without git, marked by a README, with one test.
function plainProject(root = tmp()) {
  write(path.join(root, 'README.md'), 'x')
  write(path.join(root, 'tests', 'own.test.js'), 'original')
  return root
}

describe('starting a flow', () => {
  for (const args of [['red'], ['lock'], ['init-check', 'echo ok']]) {
    it(`${args[0]} refuses a folder that only groups projects and writes nothing`, () => {
      const root = workspace()
      const result = cli(root, ...args)
      assert.notEqual(result.status, 0, result.stdout)
      assert.match(result.stdout, /Projeto A/)
      assert.match(result.stdout, /--dir/)
      assert.ok(!fs.existsSync(path.join(root, '.claude')), 'nothing may be written in the grouping folder')
    })
  }

  it('--force starts the flow there when the user confirms that folder is the project', () => {
    const root = workspace()
    const result = cli(root, 'red', '--force')
    assert.equal(result.status, 0, result.stdout)
    assert.equal(stateOf(root)?.phase, 'red')
  })

  it('refuses to start under a parent folder that already has a flow and leaves both untouched', () => {
    const parent = plainProject()
    const child = plainProject(path.join(parent, 'sub'))
    assert.equal(cli(parent, 'lock').status, 0)
    const before = fs.readFileSync(path.join(parent, '.claude', 'oracle', 'state.json'), 'utf8')
    for (const args of [['red'], ['lock'], ['init-check', 'echo ok']]) {
      const result = cli(os.tmpdir(), ...args, '--dir', child)
      assert.notEqual(result.status, 0, `${args[0]}: ${result.stdout}`)
      assert.ok(result.stdout.includes(parent), result.stdout)
      assert.match(result.stdout, /unlock/)
    }
    assert.equal(fs.readFileSync(path.join(parent, '.claude', 'oracle', 'state.json'), 'utf8'), before)
    assert.ok(!fs.existsSync(path.join(child, '.claude')))
  })

  it('starts in a project that has a project file even when it contains nested repositories', () => {
    const project = tmp()
    write(path.join(project, 'CLAUDE.md'), 'x')
    write(path.join(project, 'tests', 'own.test.js'), 'x')
    minimalGit(path.join(project, 'vendor'))
    write(path.join(project, 'vendor', 'tests', 'other.test.js'), 'x')
    const result = cli(project, 'lock')
    assert.equal(result.status, 0, result.stdout)
    assert.deepEqual(Object.keys(stateOf(project).files), ['tests/own.test.js'])
  })

  it('starts in a folder with code at its root even without a project file and with a subproject inside', () => {
    const project = tmp()
    write(path.join(project, 'render.py'), 'print(1)')
    write(path.join(project, 'test_render.py'), 'def test_x(): pass')
    write(path.join(project, 'Ferramenta', 'package.json'), '{}')
    const result = cli(project, 'lock')
    assert.equal(result.status, 0, result.stdout)
    assert.deepEqual(Object.keys(stateOf(project).files), ['test_render.py'])
  })

  it('starts in a plain folder that has no project file and no subprojects, only code in subfolders', () => {
    const folder = tmp()
    write(path.join(folder, 'tests', 'a.test.js'), 'a')
    write(path.join(folder, 'src', 'app.js'), 'x')
    assert.equal(cli(folder, 'lock').status, 0)
    assert.equal(stateOf(folder)?.phase, 'locked')
  })

  it('inside a git repository it starts at the repository toplevel', () => {
    const repo = tmp()
    minimalGit(repo)
    write(path.join(repo, 'tests', 'a.test.js'), 'a')
    fs.mkdirSync(path.join(repo, 'src'))
    assert.equal(cli(path.join(repo, 'src'), 'lock').status, 0)
    assert.ok(fs.existsSync(path.join(repo, '.git', 'claude-oracle', 'state.json')))
    assert.ok(!fs.existsSync(path.join(repo, 'src', '.claude')))
  })
})

describe('continuing a flow', () => {
  it('status, restore, relock, and unlock find the flow from a subfolder', () => {
    const project = plainProject()
    const deep = path.join(project, 'src', 'deep')
    fs.mkdirSync(deep, { recursive: true })
    assert.equal(cli(project, 'lock').status, 0)
    assert.equal(projectLine(cli(deep, 'status')), `Projeto: ${project}`)
    write(path.join(project, 'tests', 'own.test.js'), 'changed')
    assert.equal(cli(deep, 'restore').status, 0)
    assert.equal(fs.readFileSync(path.join(project, 'tests', 'own.test.js'), 'utf8'), 'original')
    assert.equal(cli(deep, 'relock').status, 0)
    assert.equal(cli(deep, 'unlock').status, 0)
    assert.equal(stateOf(project), null)
    assert.ok(!fs.existsSync(path.join(deep, '.claude')))
  })
})

describe('a folder with its own flow is another project', () => {
  it('is left out of the parent lock and of the parent fingerprint', () => {
    const parent = plainProject()
    const child = plainProject(path.join(parent, 'sub'))
    assert.equal(cli(child, 'lock').status, 0)
    assert.equal(cli(parent, 'lock').status, 0)
    assert.deepEqual(Object.keys(stateOf(parent).files), ['tests/own.test.js'])
    const project = { root: parent, stateDir: path.join(parent, '.claude', 'oracle'), isGit: false }
    const before = worktreeFingerprint(project)
    write(path.join(child, 'src', 'x.js'), 'changed')
    assert.equal(worktreeFingerprint(project), before)
  })
})
