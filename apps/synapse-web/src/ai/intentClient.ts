import { INTENT_URL } from '../config'

export type IntentReason = 'not_about_business' | 'not_sure' | 'no_scenarios' | 'nothing_matched'

export type IntentScenario = { id: string; probability: number; clause: string }

export type IntentReading = {
  domain: string | null
  domainProbability: number
  problem: 'cannot_answer' | null
  reason: IntentReason | null
  scenarios: IntentScenario[]
  didYouMean: string[]
}

export type IntentClient = {
  ask: (question: string) => Promise<IntentReading>
}

export class IntentUnavailable extends Error {}

const TIMEOUT_MS = 10000
const REASONS: IntentReason[] = ['not_about_business', 'not_sure', 'no_scenarios', 'nothing_matched']

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === 'string')

function parseScenario(value: unknown): IntentScenario {
  if (!isRecord(value) || typeof value.id !== 'string' || typeof value.probability !== 'number' || typeof value.clause !== 'string') throw new IntentUnavailable('unreadable scenario')
  return { id: value.id, probability: value.probability, clause: value.clause }
}

export function parseReading(body: unknown): IntentReading {
  if (!isRecord(body) || typeof body.domain_probability !== 'number' || !Array.isArray(body.scenarios) || !strings(body.did_you_mean)) throw new IntentUnavailable('unreadable answer')
  if (body.domain !== null && typeof body.domain !== 'string') throw new IntentUnavailable('unreadable answer')
  if (body.problem !== null && body.problem !== 'cannot_answer') throw new IntentUnavailable('unreadable answer')
  const reason = body.reason === null ? null : REASONS.find((name) => name === body.reason)
  if (reason === undefined) throw new IntentUnavailable('unreadable answer')
  return { domain: body.domain, domainProbability: body.domain_probability, problem: body.problem, reason, scenarios: body.scenarios.map(parseScenario), didYouMean: body.did_you_mean }
}

export class HttpIntentClient implements IntentClient {
  async ask(question: string) {
    let response: Response
    try {
      response = await fetch(`${INTENT_URL}/v1/intent/match`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      })
    } catch {
      throw new IntentUnavailable('not reached')
    }
    if (!response.ok) throw new IntentUnavailable(`status ${response.status}`)
    return parseReading(await response.json().catch(() => null))
  }
}

export class MockIntentClient implements IntentClient {
  private reading: IntentReading | Error
  calls: string[] = []

  constructor(reading: IntentReading | Error = new IntentUnavailable('mock')) {
    this.reading = reading
  }

  async ask(question: string) {
    this.calls.push(question)
    if (this.reading instanceof Error) throw this.reading
    return this.reading
  }
}
