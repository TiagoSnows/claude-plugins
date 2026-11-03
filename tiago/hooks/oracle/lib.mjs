// Shared code for the test-oracle hooks (guard, detector, stop-gate) and the oracle.mjs CLI.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

export const ORACLE_AGENT = 'test-oracle'
// Plugin subagents report a plugin-scoped agent_type (tiago:test-oracle), loose copies the bare name.
export const isOracleAgent = type => type === ORACLE_AGENT || type === `tiago:${ORACLE_AGENT}`
// Subagents that edit code and must pass the gate before they stop.
export const GATED_SUBAGENTS = ['pbes-editor', 'pbes:pbes-editor']
// More retries against tests increase cheating (ImpossibleBench) and debugging decays after 2-3 tries.
export const MAX_CONSECUTIVE_BLOCKS = 2
export const CLI = `node "${fileURLToPath(new URL('./oracle.mjs', import.meta.url)).replace(/\\/g, '/')}"`

const MAX_BUFFER = 64 * 1024 * 1024

export async function readInput() {
  const chunks = []
  for await (const chunk of process.stdin) chunks.push(chunk)
  const raw = Buffer.concat(chunks).toString('utf8').trim()
  return raw ? JSON.parse(raw) : {}
}

export const sha256 = data => crypto.createHash('sha256').update(data).digest('hex')

// Finds .git walking up from `start`; in a worktree .git is a file containing "gitdir: <path>".
function findGit(start) {
  let dir = path.resolve(start)
  for (;;) {
    const dotGit = path.join(dir, '.git')
    if (fs.existsSync(dotGit)) {
      if (fs.statSync(dotGit).isDirectory()) return { root: dir, gitDir: dotGit }
      const match = fs.readFileSync(dotGit, 'utf8').match(/^gitdir:\s*(.+?)\s*$/m)
      if (match) return { root: dir, gitDir: path.resolve(dir, match[1]) }
    }
    const parent = path.dirname(dir)
    if (parent === dir) return null
    dir = parent
  }
}

// State lives inside .git so it never ends up in a commit.
export function projectOf(start) {
  const git = findGit(start)
  if (git) return { root: git.root, stateDir: path.join(git.gitDir, 'claude-oracle'), isGit: true }
  const root = path.resolve(start)
  return { root, stateDir: path.join(root, '.claude', 'oracle'), isGit: false }
}

const statePath = project => path.join(project.stateDir, 'state.json')
export const snapshotDir = project => path.join(project.stateDir, 'snapshot')

export function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch {
    return null
  }
}

export function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value, null, 2))
}

export const readState = project => readJson(statePath(project))
export const writeState = (project, state) => writeJson(statePath(project), state)

export function clearState(project) {
  fs.rmSync(statePath(project), { force: true })
  fs.rmSync(snapshotDir(project), { recursive: true, force: true })
}

const TEST_DIR = /(^|\/)(tests?|__tests__|specs?|e2e|cypress)\//i
const TEST_FILE = /\.(test|spec)\.[cm]?[jt]sx?$|(^|\/)test_[^/]*\.py$|_test\.(py|go)$|(^|\/)conftest\.py$/i
const JVM_DOTNET_TEST = /[a-z0-9]Tests?\.(java|kt|cs)$/
const TEST_CONFIG =
  /(^|\/)(pytest\.ini|jest\.config\.[^/]+|vitest\.config\.[^/]+|playwright\.config\.[^/]+|cypress\.config\.[^/]+|karma\.conf\.[^/]+|\.mocharc[^/]*|phpunit\.xml[^/]*)$/i

// `rel` is relative to the project root, with forward slashes.
export const isTestPath = rel =>
  TEST_DIR.test(rel) || TEST_FILE.test(rel) || JVM_DOTNET_TEST.test(rel) || TEST_CONFIG.test(rel)

export function relativeTo(project, file) {
  const rel = path.relative(project.root, path.resolve(file)).replace(/\\/g, '/')
  return rel.startsWith('..') || path.isAbsolute(rel) ? null : rel
}

const SKIP_DIRS = new Set(['node_modules', '.git', '.venv', 'venv', 'dist', 'build', '__pycache__', '.next', 'target', '.tox'])

function walk(root, dir = '', out = []) {
  if (out.length > 20000) return out
  for (const entry of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue
    const rel = dir ? `${dir}/${entry.name}` : entry.name
    if (entry.isDirectory()) walk(root, rel, out)
    else out.push(rel)
  }
  return out
}

export function listTestFiles(project) {
  let files
  if (project.isGit) {
    const result = spawnSync('git', ['-C', project.root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], {
      encoding: 'utf8',
      maxBuffer: MAX_BUFFER,
    })
    files = result.status === 0 ? result.stdout.split('\0').filter(Boolean) : walk(project.root)
  } else {
    files = walk(project.root)
  }
  return [...new Set(files)].filter(isTestPath).filter(rel => fs.existsSync(path.join(project.root, rel)))
}

// Test configuration that lives inside general files (package.json, pyproject.toml).
function embeddedTestConfig(project) {
  const out = {}
  const pkg = readJson(path.join(project.root, 'package.json'))
  if (pkg) out['package.json#test-config'] = JSON.stringify({ test: pkg.scripts?.test, jest: pkg.jest, mocha: pkg.mocha, vitest: pkg.vitest })
  const pyproject = path.join(project.root, 'pyproject.toml')
  if (fs.existsSync(pyproject)) {
    const match = fs.readFileSync(pyproject, 'utf8').match(/^\[tool\.pytest\.ini_options\][\s\S]*?(?=^\[|(?![\s\S]))/m)
    out['pyproject.toml#tool.pytest.ini_options'] = match ? match[0] : ''
  }
  return out
}

export function takeSnapshot(project) {
  const files = {}
  fs.rmSync(snapshotDir(project), { recursive: true, force: true })
  for (const rel of listTestFiles(project)) {
    const content = fs.readFileSync(path.join(project.root, rel))
    files[rel] = sha256(content)
    const copy = path.join(snapshotDir(project), rel)
    fs.mkdirSync(path.dirname(copy), { recursive: true })
    fs.writeFileSync(copy, content)
  }
  const embedded = Object.fromEntries(Object.entries(embeddedTestConfig(project)).map(([key, value]) => [key, sha256(value)]))
  return { files, embedded }
}

export function diffSnapshot(project, state) {
  const changed = []
  const removed = []
  for (const [rel, hash] of Object.entries(state.files ?? {})) {
    const file = path.join(project.root, rel)
    if (!fs.existsSync(file)) removed.push(rel)
    else if (sha256(fs.readFileSync(file)) !== hash) changed.push(rel)
  }
  const added = listTestFiles(project).filter(rel => !(rel in (state.files ?? {})))
  const current = embeddedTestConfig(project)
  const config = Object.entries(state.embedded ?? {})
    .filter(([key, hash]) => sha256(current[key] ?? '') !== hash)
    .map(([key]) => key)
  return { changed, removed, added, config, clean: !changed.length && !removed.length && !added.length && !config.length }
}

export function readCheckConfig(project) {
  const config = readJson(path.join(project.root, '.claude', 'check.json'))
  return config?.command ? config : null
}

// Where Git for Windows keeps bash.exe, relative to its install folder.
const GIT_BASH = [path.join('usr', 'bin', 'bash.exe'), path.join('bin', 'bash.exe')]

// On Windows a bare `bash` resolves to the WSL launcher in System32, which fails ("execvpe(/bin/bash) failed") when no
// distro is installed, and Git Bash is rarely on PATH. Look in the usual install folders and next to the git.exe on PATH.
function findGitBash() {
  const installs = ['ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)']
    .map(name => process.env[name])
    .filter(Boolean)
    .map(dir => path.join(dir, 'Git'))
  if (process.env.LOCALAPPDATA) installs.push(path.join(process.env.LOCALAPPDATA, 'Programs', 'Git'))
  for (const dir of (process.env.PATH ?? '').split(path.delimiter)) {
    if (dir && fs.existsSync(path.join(dir, 'git.exe'))) installs.push(path.resolve(dir, '..'), path.resolve(dir, '..', '..'))
  }
  for (const install of installs) {
    for (const rel of GIT_BASH) if (fs.existsSync(path.join(install, rel))) return path.join(install, rel)
  }
  return null
}

// "shell" in .claude/check.json: "bash" (Git Bash on Windows) or the full path of a bash/sh/zsh executable, used as is.
const isBashShell = shell =>
  typeof shell === 'string' && (shell === 'bash' || (path.isAbsolute(shell) && /^(ba|z)?sh(\.exe)?$/i.test(path.basename(shell))))
const bashFor = shell => (shell !== 'bash' ? shell : process.platform === 'win32' ? findGitBash() : 'bash')

export function runCheck(project, config) {
  const options = {
    cwd: project.root,
    encoding: 'utf8',
    timeout: (config.timeoutSec ?? 300) * 1000,
    maxBuffer: MAX_BUFFER,
    env: { ...process.env, CI: '1', FORCE_COLOR: '0', NO_COLOR: '1' },
  }
  let result
  if (config.shell === 'powershell') result = spawnSync('powershell', ['-NoProfile', '-Command', config.command], options)
  else if (isBashShell(config.shell)) {
    const bash = bashFor(config.shell)
    result = bash
      ? spawnSync(bash, ['-lc', config.command], options)
      : { status: null, error: new Error('Git Bash não encontrado. Instale o Git for Windows ou ponha o caminho completo do bash.exe em "shell" no .claude/check.json.') }
  } else result = spawnSync(config.command, { ...options, shell: true })
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}${result.error ? `\n${result.error.message}` : ''}`
  return { ok: result.status === 0, code: result.status, output }
}

// Keeps only failure lines plus the tail, so the agent doesn't read the whole test log.
export function summarizeFailures(output) {
  const lines = output.replace(/\x1b\[[0-9;]*m/g, '').split(/\r?\n/)
  const failure = /FAIL|Error|ERROR|error[:\s]|Assertion|Traceback|✗|✕|×|●|panicked|failed|Exception/
  const keep = new Set()
  lines.forEach((line, i) => {
    if (failure.test(line)) for (let k = i; k < Math.min(i + 3, lines.length); k++) keep.add(k)
  })
  const picked = [...keep].sort((a, b) => a - b).slice(0, 60)
  const tail = lines
    .map((line, i) => [line, i])
    .filter(([line, i]) => line.trim() && !keep.has(i))
    .slice(-15)
    .map(([line]) => line)
  return [...picked.map(i => lines[i]), ...(tail.length ? ['[...]', ...tail] : [])].join('\n').slice(0, 6000)
}

// Changes since HEAD; null when the tree is clean (nothing for the gate to verify).
export function worktreeFingerprint(project) {
  if (!project.isGit) return 'no-git'
  const git = args => spawnSync('git', ['-C', project.root, ...args], { encoding: 'utf8', maxBuffer: MAX_BUFFER })
  const status = git(['status', '--porcelain=v1', '-z', '--untracked-files=all'])
  if (status.status !== 0 || !status.stdout) return null
  let diff = git(['diff', 'HEAD', '--no-color'])
  if (diff.status !== 0) diff = git(['diff', '--no-color'])
  const untracked = status.stdout
    .split('\0')
    .filter(entry => entry.startsWith('?? '))
    .map(entry => {
      const rel = entry.slice(3)
      try {
        const stat = fs.statSync(path.join(project.root, rel))
        return `${rel}:${stat.size}:${stat.mtimeMs}`
      } catch {
        return rel
      }
    })
  return sha256(`${status.stdout}\n${diff.stdout ?? ''}\n${untracked.join('|')}`)
}
