import { registry } from '@sami/ui'

export type AiBoard = { name: string; widgets: { widget: string; props: object }[] }

export type AiBoardResult = { ok: true; board: AiBoard } | { ok: false; error: string }

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)

export function parseAiBoard(text: string): AiBoardResult {
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    return { ok: false, error: 'Not valid JSON' }
  }
  if (!isRecord(parsed) || typeof parsed.name !== 'string' || !parsed.name.trim()) return { ok: false, error: 'Board needs a name' }
  if (!Array.isArray(parsed.widgets) || parsed.widgets.length === 0) return { ok: false, error: 'Board needs at least one widget' }
  const widgets: AiBoard['widgets'] = []
  for (const [index, item] of parsed.widgets.entries()) {
    if (!isRecord(item) || typeof item.widget !== 'string' || !isRecord(item.props)) return { ok: false, error: `Widget ${index + 1} needs widget and props` }
    if (!registry.names().includes(item.widget)) return { ok: false, error: `Widget ${index + 1}: unknown widget ${item.widget}` }
    if (!registry.validate(item.widget, item.props)) return { ok: false, error: `Widget ${index + 1}: props do not fit ${item.widget}` }
    widgets.push({ widget: item.widget, props: item.props })
  }
  return { ok: true, board: { name: parsed.name.trim(), widgets } }
}
