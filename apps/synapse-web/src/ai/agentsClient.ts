import { AGENTS_URL } from '../config'

export type TextBlock = { type: 'text'; lines: string[] }
export type TrendBlock = { type: 'trend'; metric: string; currency: string; points: { month: string; value: string }[]; marked: string[] }
export type TableBlock = { type: 'table'; title: string; columns: string[]; rows: Record<string, string | null>[] }
export type EvidenceStep = { summary: string; rows: Record<string, unknown>[] }
export type EvidenceBlock = { type: 'evidence'; finding: string; steps: EvidenceStep[] }
export type AnswerBlock = TextBlock | TrendBlock | TableBlock | EvidenceBlock

export type AgentAnswer = {
  readable: boolean
  problem: 'unreadable' | 'not_finished' | null
  label: string | null
  blocks: AnswerBlock[]
}

export type AgentsClient = {
  ask: (question: string) => Promise<AgentAnswer>
}

export class AgentsUnavailable extends Error {}

const TIMEOUT_MS = 30000

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === 'string')
const records = (value: unknown): value is Record<string, unknown>[] => Array.isArray(value) && value.every(isRecord)

function parseBlock(block: unknown): AnswerBlock | null {
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
  return null
}

export function parseAnswer(body: unknown): AgentAnswer {
  if (!isRecord(body) || !Array.isArray(body.blocks)) throw new AgentsUnavailable('unreadable answer')
  const problem = body.problem === 'unreadable' || body.problem === 'not_finished' ? body.problem : null
  const blocks = body.blocks.map(parseBlock).filter((block): block is AnswerBlock => block !== null)
  return { readable: body.readable === true, problem, label: typeof body.label === 'string' ? body.label : null, blocks }
}

export class HttpAgentsClient implements AgentsClient {
  async ask(question: string) {
    let response: Response
    try {
      response = await fetch(`${AGENTS_URL}/v1/agents/analyse`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      })
    } catch {
      throw new AgentsUnavailable('not reached')
    }
    if (!response.ok) throw new AgentsUnavailable(`status ${response.status}`)
    return parseAnswer(await response.json().catch(() => null))
  }
}

export class MockAgentsClient implements AgentsClient {
  private answer: AgentAnswer | Error

  constructor(answer: AgentAnswer | Error) {
    this.answer = answer
  }

  async ask() {
    if (this.answer instanceof Error) throw this.answer
    return this.answer
  }
}
