import { registry } from '@sami/ui'
import { parseAiBoard } from '../src/ai/parseAiBoard'
import { fixtures } from '../src/catalog/fixtures'

const described = registry.describe()

describe('widget list for a model', () => {
  it('survives a JSON round trip', () => {
    expect(JSON.parse(JSON.stringify(described))).toEqual(JSON.parse(JSON.stringify(described)))
    expect(described.length).toBe(registry.names().length)
  })

  it('has a one-sentence description and a size for every widget', () => {
    for (const entry of described) {
      expect(entry.description.length).toBeGreaterThan(20)
      expect(entry.description.split('. ').length).toBeLessThanOrEqual(3)
      expect(entry.size.defaultW).toBeGreaterThan(0)
    }
  })

  it('names and descriptions fit a small model prompt (estimate 4 characters per token)', () => {
    const prompt = described.map((entry) => `${entry.name}: ${entry.description}`).join('\n')
    expect(prompt.length / 4).toBeLessThan(600)
  })

  it('has no style, colour or pixel props in any schema', () => {
    const keys = JSON.stringify(described.map((entry) => entry.schema))
    for (const word of ['"color"', '"style"', '"className"', '"width"', '"height"']) expect(keys).not.toContain(word)
  })
})

describe('catalog props against the widget schemas', () => {
  it.each(fixtures)('$entry.id validates', ({ entry, props }) => {
    expect(registry.validate(entry.widget, props)).toBe(true)
  })
})

describe('parseAiBoard', () => {
  const good = (widgets: unknown[] = [{ widget: 'KpiCard', props: { title: 'Sales', value: 10 } }]) => JSON.stringify({ name: ' Sales ', widgets })

  it('accepts a model-written board and trims the name', () => {
    const result = parseAiBoard(good())
    expect(result).toEqual({ ok: true, board: { name: 'Sales', widgets: [{ widget: 'KpiCard', props: { title: 'Sales', value: 10 } }] } })
  })

  it.each([
    ['text that is not JSON', 'here is your board', 'Not valid JSON'],
    ['a missing name', JSON.stringify({ widgets: [] }), 'name'],
    ['an empty board', good([]), 'at least one'],
    ['an unknown widget', good([{ widget: 'PieOfDoom', props: {} }]), 'unknown widget'],
    ['bad props', good([{ widget: 'KpiCard', props: { title: 'x' } }]), 'do not fit'],
    ['a widget without props', good([{ widget: 'KpiCard' }]), 'needs widget and props'],
  ])('rejects %s', (_name, text, message) => {
    const result = parseAiBoard(text)
    expect(result.ok).toBe(false)
    expect(!result.ok && result.error).toContain(message)
  })

  it('accepts every catalog entry as a widget', () => {
    const widgets = fixtures.map(({ entry, props }) => ({ widget: entry.widget, props }))
    expect(parseAiBoard(good(widgets)).ok).toBe(true)
  })

  it('offers an object JSON schema with properties for every widget', () => {
    for (const entry of described) {
      const schema = entry.schema as { type?: string; properties?: object }
      expect(schema.type).toBe('object')
      expect(Object.keys(schema.properties ?? {}).length).toBeGreaterThan(0)
    }
  })
})
