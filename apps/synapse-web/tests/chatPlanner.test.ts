import { MockChatPlanner } from '../src/ai/chatPlanner'
import { fixtureEntries } from '../src/catalog/fixtures'

const entries = fixtureEntries

const planner = new MockChatPlanner()

describe('asking a question', () => {
  it('returns the widgets a topic word matches, at most four', async () => {
    const answer = await planner.plan('show me top customers', entries)
    expect(answer.catalogIds).toContain('top-customers')
    expect(answer.catalogIds.length).toBeLessThanOrEqual(4)
    expect(answer.board).toBeUndefined()
  })

  it('says so when nothing matches', async () => {
    const answer = await planner.plan('zebra', entries)
    expect(answer.catalogIds).toEqual([])
    expect(answer.reply).toMatch(/could not match/)
  })
})

describe('@builder', () => {
  it('builds a domain board with a name', async () => {
    const answer = await planner.plan('@builder build me an inventory board', entries)
    expect(answer.board?.name).toBe('Inventory review')
    expect(answer.board?.catalogIds.length).toBeGreaterThan(1)
    expect(answer.catalogIds).toEqual([])
  })

  it('builds from matching words when no domain is named', async () => {
    const answer = await planner.plan('@builder top customers', entries)
    expect(answer.board?.name).toBe('My board')
    expect(answer.board?.catalogIds).toContain('top-customers')
  })

  it('explains what to ask when there is nothing to build', async () => {
    const answer = await planner.plan('@builder', entries)
    expect(answer.board).toBeUndefined()
    expect(answer.reply).toMatch(/Tell me what to build/)
  })
})
