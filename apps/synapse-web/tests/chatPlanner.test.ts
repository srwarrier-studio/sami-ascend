import { MockChatPlanner } from '../src/ai/chatPlanner'
import { applyOps } from '../src/boards/layout'

const planner = new MockChatPlanner()
const ids = (widgets: { catalogId: string }[]) => widgets.map((widget) => widget.catalogId)

describe('asking for widgets', () => {
  it('adds the widgets a topic word matches', async () => {
    const plan = await planner.plan('show me top customers', [])
    expect(applyOps([], plan.ops).map((widget) => widget.catalogId)).toContain('top-customers')
  })

  it('does not add a widget that is already on the canvas', async () => {
    const canvas = [{ id: 'a', catalogId: 'top-customers' }]
    const plan = await planner.plan('top customers', canvas)
    expect(ids(applyOps(canvas, plan.ops)).filter((id) => id === 'top-customers')).toHaveLength(1)
  })

  it('says so when nothing matches and changes nothing', async () => {
    const plan = await planner.plan('zebra', [])
    expect(plan.ops).toEqual([])
    expect(plan.reply).toMatch(/could not match/)
  })
})

describe('building a board', () => {
  it('fills the canvas with a domain and suggests a name', async () => {
    const plan = await planner.plan('build me an inventory board', [{ id: 'a', catalogId: 'sales-today' }])
    const next = applyOps([{ id: 'a', catalogId: 'sales-today' }], plan.ops)
    expect(next.length).toBeGreaterThan(1)
    expect(ids(next)).not.toContain('sales-today')
    expect(plan.boardName).toBe('Inventory review')
  })
})

describe('editing the canvas', () => {
  const canvas = [
    { id: 'a', catalogId: 'top-customers' },
    { id: 'b', catalogId: 'day-sales' },
  ]

  it('clears on start over', async () => {
    expect(applyOps(canvas, (await planner.plan('start over', canvas)).ops)).toEqual([])
  })

  it('removes the widget named', async () => {
    expect(ids(applyOps(canvas, (await planner.plan('remove top customers', canvas)).ops))).toEqual(['day-sales'])
  })

  it('makes the last widget bigger', async () => {
    const next = applyOps(canvas, (await planner.plan('make it bigger', canvas)).ops)
    expect(next[1].size).toBeDefined()
    expect(next[0].size).toBeUndefined()
  })
})
