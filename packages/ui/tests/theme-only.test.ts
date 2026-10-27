import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const forbidden: [string, RegExp][] = [
  ['inline style prop', /\bstyle\s*=\s*\{/],
  ['inline style object', /\bstyle\s*:\s*\{/],
  ['hex color', /#[0-9a-fA-F]{3,8}\b/],
  ['rgb/hsl color', /\b(rgb|rgba|hsl|hsla)\(/],
  ['px value', /\b\d+px\b/],
]

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    return entry.isDirectory() ? files(path) : [path]
  })
}

describe('styles flow from the theme only', () => {
  const sources = ['src', 'playground']
    .flatMap((dir) => files(dir))
    .filter((f) => /\.(tsx?|css)$/.test(f) && !f.endsWith('palettes.ts'))

  it.each(forbidden)('has no %s', (_name, pattern) => {
    const offenders = sources.filter((file) => pattern.test(readFileSync(file, 'utf8')))
    expect(offenders).toEqual([])
  })
})
