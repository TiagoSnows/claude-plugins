// PostToolUse (Edit|Write): reports newly introduced patterns that make checks pass without exercising behavior.
// Signatures from Anthropic/Redwood (arXiv 2511.18397) and OpenAI (arXiv 2503.11926) reward-hacking reports.
import path from 'node:path'
import { readInput, projectOf, relativeTo, isTestPath } from './lib.mjs'

const TEST_ONLY = [
  [/\bsys\.exit\s*\(|\bos\._exit\s*\(|\bprocess\.exit\s*\(/g, 'saída do processo dentro do teste (sys.exit/os._exit/process.exit)'],
  [/pytest\.skip\s*\(|@pytest\.mark\.(skip|skipif|xfail)\b|unittest\.skip|\bSkipTest\b/g, 'skip/xfail'],
  [/\b(it|test|describe)\.(skip|only|todo)\s*\(|\b(xit|xdescribe|xtest|fit|fdescribe)\s*\(/g, 'skip/only em teste JS'],
  [/TestReport|pytest_runtest_makereport|pytest_collection_modifyitems/g, 'manipulação de relatório ou coleta do pytest'],
  [/def\s+__eq__\s*\([^)]*\)[^:]*:\s*return\s+True\b/g, '__eq__ que sempre retorna True'],
  [/expect\s*\(\s*true\s*\)\s*\.\s*toBe\s*\(\s*true\s*\)|\bassert\s+True\b/g, 'assert trivial'],
]
const ANYWHERE = [
  [/(\/\/|\/\*)\s*@ts-(ignore|nocheck|expect-error)/g, 'supressão do TypeScript'],
  [/(\/\/|\/\*)\s*eslint-disable/g, 'eslint-disable'],
  [/#\s*type:\s*ignore|#\s*noqa|#\s*pragma:\s*no cover|(\/\/|\/\*)\s*(istanbul|c8)\s+ignore/g, 'supressão de checagem ou cobertura'],
  [/\bas\s+any\b|\bas\s+unknown\s+as\b/g, 'cast forçado (as any / as unknown as)'],
]

// Only code: docs and rules that mention these patterns (e.g. "never use @ts-ignore") are not edits that bypass checks.
const CODE_FILE =
  /\.([cm]?[jt]sx?|py|pyi|go|rs|dart|kt|kts|swift|java|scala|rb|php|sql|vue|svelte|c|h|cc|cpp|cxx|hh|hpp|cs|sh|bash|zsh|ps1|psm1|ex|exs|lua)$/i

const count = (text, pattern) => (text.match(pattern) ?? []).length

try {
  const input = await readInput()
  const toolInput = input.tool_input ?? {}
  if (!toolInput.file_path || !CODE_FILE.test(toolInput.file_path)) process.exit(0)

  const before = input.tool_name === 'Edit' ? toolInput.old_string ?? '' : ''
  const after = input.tool_name === 'Edit' ? toolInput.new_string ?? '' : toolInput.content ?? ''
  const project = projectOf(path.dirname(path.resolve(toolInput.file_path)))
  const rel = relativeTo(project, toolInput.file_path) ?? path.basename(toolInput.file_path)

  const patterns = isTestPath(rel) ? [...TEST_ONLY, ...ANYWHERE] : ANYWHERE
  const found = patterns.filter(([pattern]) => count(after, pattern) > count(before, pattern)).map(([, label]) => label)
  if (!found.length) process.exit(0)

  const context = `A edição em ${rel} introduziu: ${found.join('; ')}. São padrões conhecidos que fazem testes ou checks passarem sem exercitar o comportamento.`
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: context } }))
} catch (error) {
  process.stderr.write(`oracle detector: ${error.message}\n`)
  process.exit(0)
}
