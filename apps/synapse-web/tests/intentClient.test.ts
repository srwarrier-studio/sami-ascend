import { HttpIntentClient, IntentDataUnavailable, IntentUnavailable, MockIntentClient, parseReading, parseReply } from '../src/ai/intentClient'

const respond = (status: number, body: unknown = {}) => vi.fn(async () => new Response(JSON.stringify(body), { status }))

const stub = (fetchMock: ReturnType<typeof respond>) => {
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

const answered = {
  problem: null,
  reason: null,
  domain: 'Sales',
  domain_probability: 0.95,
  domain_scores: { Sales: 0.95 },
  offered: ['sales_value'],
  scenarios: [{ id: 'sales_value', probability: 0.64, clause: 'What were sales for August?' }],
  did_you_mean: [],
}

const text = { type: 'text', lines: ['Sales for June 2026 were INR 600.'] }
const table = { type: 'table', title: 'Top customers, June 2026', columns: ['Name', 'Current'], rows: [{ name: 'Kestrel Logistics', current: '400' }] }
const trend = { type: 'trend', metric: 'sales', currency: 'INR', points: [{ month: '2026-05', value: '500' }], marked: [] }

const reply = (overrides: Record<string, unknown> = {}) => ({
  problem: null,
  reason: null,
  periods: [],
  reading: answered,
  answers: [{ scenario: 'sales_value', blocks: [text] }],
  ...overrides,
})

describe('asking intent-api for an answer', () => {
  it('sends the chosen company with the question', async () => {
    const fetchMock = stub(respond(200, reply()))
    await new HttpIntentClient().answer('Sales?', 'organica')
    expect(JSON.parse((fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].body as string)).toEqual({ question: 'Sales?', company: 'organica' })
  })

  it('posts the question with credentials to the answer route and returns the reading and the blocks', async () => {
    const fetchMock = stub(respond(200, reply()))
    const result = await new HttpIntentClient().answer('What were sales for August?', null)
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8006/v1/intent/answer')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(JSON.parse(init.body as string)).toEqual({ question: 'What were sales for August?' })
    expect(result.reading).toEqual({ domain: 'Sales', domainProbability: 0.95, problem: null, reason: null, scenarios: [{ id: 'sales_value', probability: 0.64, clause: 'What were sales for August?' }], didYouMean: [] })
    expect(result).toMatchObject({ problem: null, reason: null, periods: [], answers: [{ scenario: 'sales_value', blocks: [text] }] })
  })

  it('reads text, table and trend blocks in order, per scenario', async () => {
    stub(respond(200, reply({ answers: [{ scenario: 'sales_top_customers', blocks: [text, table] }, { scenario: 'sales_trend', blocks: [text, trend] }] })))
    const result = await new HttpIntentClient().answer('x', null)
    expect(result.answers.map((item) => item.scenario)).toEqual(['sales_top_customers', 'sales_trend'])
    expect(result.answers[0].blocks.map((block) => block.type)).toEqual(['text', 'table'])
    expect(result.answers[1].blocks.map((block) => block.type)).toEqual(['text', 'trend'])
  })

  it('reads a refusal with its reason, the periods and no answers', async () => {
    stub(respond(200, reply({ problem: 'cannot_answer', reason: 'period_not_supported', periods: ['June 2026', 'May 2026'], answers: [] })))
    expect(await new HttpIntentClient().answer('x', null)).toMatchObject({ problem: 'cannot_answer', reason: 'period_not_supported', periods: ['June 2026', 'May 2026'], answers: [] })
  })

  it.each(['not_answerable_yet', 'not_about_business', 'not_sure', 'no_scenarios', 'nothing_matched'])('accepts the reason %s', async (reason) => {
    stub(respond(200, reply({ problem: 'cannot_answer', reason, answers: [] })))
    expect((await new HttpIntentClient().answer('x', null)).reason).toBe(reason)
  })

  it('treats a 503 with cannot_fetch_now as the figures being unavailable', async () => {
    stub(respond(503, { problem: 'cannot_fetch_now' }))
    await expect(new HttpIntentClient().answer('sales', null)).rejects.toBeInstanceOf(IntentDataUnavailable)
  })

  it('keeps cannot_classify_now as plain unavailable', async () => {
    stub(respond(503, { problem: 'cannot_classify_now' }))
    const failure = await new HttpIntentClient().answer('sales', null).catch((error) => error)
    expect(failure).toBeInstanceOf(IntentUnavailable)
    expect(failure).not.toBeInstanceOf(IntentDataUnavailable)
  })

  it.each([401, 403, 422, 500])('treats status %s as unavailable', async (status) => {
    stub(respond(status, {}))
    await expect(new HttpIntentClient().answer('sales', null)).rejects.toBeInstanceOf(IntentUnavailable)
  })

  it('treats a network error as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('failed') }))
    await expect(new HttpIntentClient().answer('sales', null)).rejects.toBeInstanceOf(IntentUnavailable)
  })

  it('treats a body that is not JSON as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html>', { status: 200 })))
    await expect(new HttpIntentClient().answer('sales', null)).rejects.toBeInstanceOf(IntentUnavailable)
  })
})

describe('parseReply', () => {
  it.each([
    ['not an object', null],
    ['periods not strings', reply({ periods: [1] })],
    ['answers not a list', reply({ answers: 'x' })],
    ['an unknown problem', reply({ problem: 'broken' })],
    ['an unknown reason', reply({ problem: 'cannot_answer', reason: 'because' })],
    ['a missing reading', reply({ reading: null })],
    ['an answer without a scenario', reply({ answers: [{ blocks: [text] }] })],
    ['an answer without blocks', reply({ answers: [{ scenario: 'a' }] })],
    ['a block of an unknown shape', reply({ answers: [{ scenario: 'a', blocks: [{ type: 'chart' }] }] })],
    ['a block that is damaged', reply({ answers: [{ scenario: 'a', blocks: [{ type: 'text', lines: 'x' }] }] })],
  ])('rejects %s', (_name, body) => {
    expect(() => parseReply(body)).toThrow(IntentUnavailable)
  })
})

describe('parseReading', () => {
  it.each([
    ['not an object', null],
    ['no probability', { ...answered, domain_probability: 'high' }],
    ['scenarios not a list', { ...answered, scenarios: 'x' }],
    ['a scenario without a probability', { ...answered, scenarios: [{ id: 'a', clause: 'b' }] }],
    ['did_you_mean not strings', { ...answered, did_you_mean: [1] }],
    ['an unknown reason', { ...answered, problem: 'cannot_answer', reason: 'because' }],
    ['an unknown problem', { ...answered, problem: 'broken' }],
    ['a domain that is not text', { ...answered, domain: 3 }],
  ])('rejects %s', (_name, body) => {
    expect(() => parseReading(body)).toThrow(IntentUnavailable)
  })
})

describe('MockIntentClient', () => {
  it('records the questions and fails when given an error', async () => {
    const mock = new MockIntentClient(new Error('down'))
    await expect(mock.answer('x', null)).rejects.toThrow('down')
    expect(mock.calls).toEqual(['x'])
  })
})
