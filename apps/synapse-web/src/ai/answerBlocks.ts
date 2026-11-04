export type TextBlock = { type: 'text'; lines: string[] }
export type TrendBlock = { type: 'trend'; metric: string; currency: string; points: { month: string; value: string }[]; marked: string[] }
export type TableBlock = { type: 'table'; title: string; columns: string[]; rows: Record<string, string | null>[] }
export type EvidenceStep = { summary: string; rows: Record<string, unknown>[] }
export type EvidenceBlock = { type: 'evidence'; finding: string; steps: EvidenceStep[] }
export type FindingItem = {
  name: string
  dimension: string
  role: 'mover' | 'offset'
  direction: 'up' | 'down' | 'flat'
  changeText: string
  amountText: string
  shareText: string | null
  priceText: string | null
  paths: string[][]
}
export type FindingsBlock = { type: 'findings'; headline: string; items: FindingItem[]; coverage: { explainedPercent: number; text: string }; notes: string[] }
export type AnswerBlock = TextBlock | TrendBlock | TableBlock | EvidenceBlock | FindingsBlock

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === 'string')
const records = (value: unknown): value is Record<string, unknown>[] => Array.isArray(value) && value.every(isRecord)

const text = (value: unknown) => (typeof value === 'string' ? value : null)

function parseItem(item: Record<string, unknown>): FindingItem | null {
  const { name, dimension, role, direction, change_text, amount_text } = item
  if (typeof name !== 'string' || typeof dimension !== 'string' || typeof change_text !== 'string' || typeof amount_text !== 'string') return null
  if (role !== 'mover' && role !== 'offset') return null
  if (direction !== 'up' && direction !== 'down' && direction !== 'flat') return null
  const paths = Array.isArray(item.paths) && item.paths.every(strings) ? (item.paths as string[][]) : []
  return { name, dimension, role, direction, changeText: change_text, amountText: amount_text, shareText: text(item.share_text), priceText: text(item.price_text), paths }
}

export function parseBlock(block: unknown): AnswerBlock | null {
  if (!isRecord(block)) return null
  if (block.type === 'text' && strings(block.lines)) return { type: 'text', lines: block.lines }
  if (block.type === 'trend' && typeof block.metric === 'string' && typeof block.currency === 'string' && records(block.points) && strings(block.marked)) {
    const points = block.points.map((point) => ({ month: String(point.month), value: String(point.value) }))
    return { type: 'trend', metric: block.metric, currency: block.currency, points, marked: block.marked }
  }
  if (block.type === 'table' && typeof block.title === 'string' && strings(block.columns) && records(block.rows)) {
    return { type: 'table', title: block.title, columns: block.columns, rows: block.rows as TableBlock['rows'] }
  }
  if (block.type === 'evidence' && typeof block.finding === 'string' && records(block.steps)) {
    const steps = block.steps.map((step) => ({ summary: String(step.summary), rows: records(step.rows) ? step.rows : [] }))
    return { type: 'evidence', finding: block.finding, steps }
  }
  if (block.type === 'findings' && typeof block.headline === 'string' && records(block.items) && isRecord(block.coverage) && strings(block.notes)) {
    const items = block.items.map(parseItem)
    if (items.some((item) => item === null)) return null
    return { type: 'findings', headline: block.headline, items: items as FindingItem[], coverage: { explainedPercent: Number(block.coverage.explained_percent), text: String(block.coverage.text) }, notes: block.notes }
  }
  return null
}
