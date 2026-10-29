import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const forbidden: [string, RegExp][] = [
  ['mantine import', /from\s+['"]@mantine\//],
  ['inline style prop', /\bstyle\s*=\s*\{/],
  ['inline style object', /\bstyle\s*:\s*\{/],
]

const files = (dir: string): string[] =>
  readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    return entry.isDirectory() ? files(path) : [path]
  })

describe('app code uses @sami/ui and the theme only', () => {
  const sources = files('src').filter((f) => /\.tsx?$/.test(f))

  it.each(forbidden)('has no %s', (_name, pattern) => {
    const offenders = sources.filter((file) => pattern.test(readFileSync(file, 'utf8')))
    expect(offenders).toEqual([])
  })
})
