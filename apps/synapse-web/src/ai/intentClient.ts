import { INTENT_URL } from '../config'
import { parseBlock } from './agentsClient'
import type { AnswerBlock } from './agentsClient'

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

export type ReplyReason = IntentReason | 'not_answerable_yet' | 'period_not_supported'

export type IntentAnswer = { scenario: string; blocks: AnswerBlock[] }

export type IntentReply = {
  reading: IntentReading
  problem: 'cannot_answer' | null
  reason: ReplyReason | null
  periods: string[]
  answers: IntentAnswer[]
}

export type IntentClient = {
  answer: (question: string, company: string | null) => Promise<IntentReply>
}

export class IntentUnavailable extends Error {}

export class IntentDataUnavailable extends IntentUnavailable {}

const TIMEOUT_MS = 20000
const REASONS: IntentReason[] = ['not_about_business', 'not_sure', 'no_scenarios', 'nothing_matched']
const REPLY_REASONS: ReplyReason[] = [...REASONS, 'not_answerable_yet', 'period_not_supported']

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

function parseAnswer(value: unknown): IntentAnswer {
  if (!isRecord(value) || typeof value.scenario !== 'string' || !Array.isArray(value.blocks)) throw new IntentUnavailable('unreadable answer')
  const blocks = value.blocks.map(parseBlock)
  if (blocks.some((block) => block === null)) throw new IntentUnavailable('unreadable block')
  return { scenario: value.scenario, blocks: blocks as AnswerBlock[] }
}

export function parseReply(body: unknown): IntentReply {
  if (!isRecord(body) || !strings(body.periods) || !Array.isArray(body.answers)) throw new IntentUnavailable('unreadable answer')
  if (body.problem !== null && body.problem !== 'cannot_answer') throw new IntentUnavailable('unreadable answer')
  const reason = body.reason === null ? null : REPLY_REASONS.find((name) => name === body.reason)
  if (reason === undefined) throw new IntentUnavailable('unreadable answer')
  return { reading: parseReading(body.reading), problem: body.problem, reason, periods: body.periods, answers: body.answers.map(parseAnswer) }
}

export class HttpIntentClient implements IntentClient {
  async answer(question: string, company: string | null) {
    let response: Response
    try {
      response = await fetch(`${INTENT_URL}/v1/intent/answer`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(company ? { question, company } : { question }),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      })
    } catch {
      throw new IntentUnavailable('not reached')
    }
    const body = await response.json().catch(() => null)
    if (response.status === 503 && isRecord(body) && body.problem === 'cannot_fetch_now') throw new IntentDataUnavailable('figures not reached')
    if (!response.ok) throw new IntentUnavailable(`status ${response.status}`)
    return parseReply(body)
  }
}

export class MockIntentClient implements IntentClient {
  private reply: IntentReply | Error
  calls: string[] = []
  companies: (string | null)[] = []

  constructor(reply: IntentReply | Error = new IntentUnavailable('mock')) {
    this.reply = reply
  }

  async answer(question: string, company: string | null) {
    this.calls.push(question)
    this.companies.push(company)
    if (this.reply instanceof Error) throw this.reply
    return this.reply
  }
}
