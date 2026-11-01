import { HttpIntentClient, IntentUnavailable, MockIntentClient, parseReading } from '../src/ai/intentClient'

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

const refused = { ...answered, problem: 'cannot_answer', reason: 'no_scenarios', domain: 'Finance', scenarios: [], did_you_mean: ['Finance', 'Sales'] }

describe('asking intent-api', () => {
  it('posts the question with credentials and returns the reading', async () => {
    const fetchMock = stub(respond(200, answered))
    const reading = await new HttpIntentClient().ask('What were sales for August?')
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8006/v1/intent/match')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(JSON.parse(init.body as string)).toEqual({ question: 'What were sales for August?' })
    expect(reading).toEqual({ domain: 'Sales', domainProbability: 0.95, problem: null, reason: null, scenarios: [{ id: 'sales_value', probability: 0.64, clause: 'What were sales for August?' }], didYouMean: [] })
  })

  it('reads a refusal with its reason and the domains to suggest', async () => {
    stub(respond(200, refused))
    const reading = await new HttpIntentClient().ask('who owes us money')
    expect(reading).toMatchObject({ problem: 'cannot_answer', reason: 'no_scenarios', domain: 'Finance', scenarios: [], didYouMean: ['Finance', 'Sales'] })
  })

  it.each([401, 403, 422, 500, 503])('treats status %s as unavailable', async (status) => {
    stub(respond(status, { problem: 'cannot_classify_now' }))
    await expect(new HttpIntentClient().ask('sales')).rejects.toBeInstanceOf(IntentUnavailable)
  })

  it('treats a network error as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('failed') }))
    await expect(new HttpIntentClient().ask('sales')).rejects.toBeInstanceOf(IntentUnavailable)
  })

  it('treats a body that is not JSON as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html>', { status: 200 })))
    await expect(new HttpIntentClient().ask('sales')).rejects.toBeInstanceOf(IntentUnavailable)
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
    await expect(mock.ask('x')).rejects.toThrow('down')
    expect(mock.calls).toEqual(['x'])
  })
})
