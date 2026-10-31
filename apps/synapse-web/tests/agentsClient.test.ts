import { AgentsUnavailable, HttpAgentsClient, MockAgentsClient, parseAnswer } from '../src/ai/agentsClient'

const respond = (status: number, body: unknown = {}) => vi.fn(async () => new Response(JSON.stringify(body), { status }))

const stub = (fetchMock: ReturnType<typeof respond>) => {
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

const answer = {
  readable: true,
  label: 'Mock data (butterfly)',
  blocks: [
    { type: 'text', lines: ['Sales fell 14.4%.'] },
    { type: 'trend', metric: 'sales', currency: 'INR', points: [{ month: '2026-07', value: '7570000' }], marked: ['2026-07'] },
    { type: 'table', title: 'By customer', columns: ['Name'], rows: [{ Name: 'Acme' }] },
    { type: 'evidence', finding: 'Acme', steps: [{ summary: 'no valid contract', rows: [{ SalesContract: '0040000127' }] }] },
  ],
}

describe('asking the agent', () => {
  it('posts the question to sami-agents with credentials and returns the parsed answer', async () => {
    const fetchMock = stub(respond(200, answer))
    const result = await new HttpAgentsClient().ask('why did sales fall in August')
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8005/v1/agents/analyse')
    expect(init.method).toBe('POST')
    expect(init.credentials).toBe('include')
    expect(JSON.parse(init.body as string)).toEqual({ question: 'why did sales fall in August' })
    expect(result.readable).toBe(true)
    expect(result.label).toBe('Mock data (butterfly)')
    expect(result.blocks.map((block) => block.type)).toEqual(['text', 'trend', 'table', 'evidence'])
  })

  it.each([401, 403, 503])('treats status %i as unavailable', async (status) => {
    stub(respond(status))
    await expect(new HttpAgentsClient().ask('x')).rejects.toBeInstanceOf(AgentsUnavailable)
  })

  it('treats a network error as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('failed'))))
    await expect(new HttpAgentsClient().ask('x')).rejects.toBeInstanceOf(AgentsUnavailable)
  })

  it('treats a body that is not an answer as unavailable', async () => {
    stub(respond(200, { nothing: true }))
    await expect(new HttpAgentsClient().ask('x')).rejects.toBeInstanceOf(AgentsUnavailable)
  })
})

describe('reading the answer', () => {
  it('keeps the problem of a refusal', () => {
    const result = parseAnswer({ readable: false, problem: 'not_finished', label: null, blocks: [{ type: 'text', lines: ['Not over.'] }] })
    expect(result).toEqual({ readable: false, problem: 'not_finished', label: null, blocks: [{ type: 'text', lines: ['Not over.'] }] })
  })

  it.each(['unreadable', 'widgets', 'not_finished', 'restricted', 'not_one_month'])('keeps the problem %s', (problem) => {
    expect(parseAnswer({ readable: false, problem, blocks: [] }).problem).toBe(problem)
  })

  it('drops a problem it does not know', () => {
    expect(parseAnswer({ readable: false, problem: 'something_new', blocks: [] }).problem).toBeNull()
  })

  it('has no problem or label when the answer carries none', () => {
    const result = parseAnswer({ readable: true, blocks: [] })
    expect(result).toEqual({ readable: true, problem: null, label: null, blocks: [] })
  })

  it('skips unknown and malformed blocks', () => {
    const result = parseAnswer({ readable: true, blocks: [{ type: 'pie' }, { type: 'text', lines: 'no' }, 5, { type: 'text', lines: ['ok'] }] })
    expect(result.blocks).toEqual([{ type: 'text', lines: ['ok'] }])
  })

  it('gives an evidence step with no rows an empty list', () => {
    const result = parseAnswer({ readable: true, blocks: [{ type: 'evidence', finding: 'A', steps: [{ summary: 's' }] }] })
    expect(result.blocks).toEqual([{ type: 'evidence', finding: 'A', steps: [{ summary: 's', rows: [] }] }])
  })
})

describe('the mock client', () => {
  it('returns the answer it was given, or throws the error', async () => {
    const given = { readable: false, problem: 'unreadable' as const, label: null, blocks: [] }
    expect(await new MockAgentsClient(given).ask()).toBe(given)
    await expect(new MockAgentsClient(new AgentsUnavailable('down')).ask()).rejects.toBeInstanceOf(AgentsUnavailable)
  })
})
