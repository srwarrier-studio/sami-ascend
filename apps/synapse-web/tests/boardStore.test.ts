import { registry } from '@sami/ui'
import { MockBoardStore } from '../src/boards/boardStore'

describe('MockBoardStore', () => {
  it('starts with the Sales overview board', async () => {
    const boards = await new MockBoardStore().list()
    expect(boards.map((board) => board.name)).toEqual(['Sales overview'])
    expect(boards[0].widgets.length).toBeGreaterThan(0)
  })

  it('creates boards with unique ids', async () => {
    const store = new MockBoardStore()
    const a = await store.create('A')
    const b = await store.create('B')
    expect(a.id).not.toBe(b.id)
    expect((await store.list()).map((board) => board.name)).toEqual(['Sales overview', 'A', 'B'])
  })

  it('renames a board', async () => {
    const store = new MockBoardStore()
    await store.rename('board-1', 'Revenue')
    expect((await store.list())[0].name).toBe('Revenue')
  })

  it('removes a board', async () => {
    const store = new MockBoardStore()
    const extra = await store.create('Extra')
    await store.remove(extra.id)
    expect((await store.list()).map((board) => board.id)).toEqual(['board-1'])
  })

  it('saves the widget order', async () => {
    const store = new MockBoardStore()
    await store.saveWidgets('board-1', [{ id: 'x', catalogId: 'top-customers' }])
    expect((await store.list())[0].widgets).toEqual([{ id: 'x', catalogId: 'top-customers' }])
  })

  it('does not let callers change the stored list', async () => {
    const store = new MockBoardStore()
    ;(await store.list())[0].widgets.length = 0
    expect((await store.list())[0].widgets.length).toBeGreaterThan(0)
  })

  it.each([
    ['rename', (store: MockBoardStore) => store.rename('nope', 'x')],
    ['remove', (store: MockBoardStore) => store.remove('nope')],
    ['saveWidgets', (store: MockBoardStore) => store.saveWidgets('nope', [])],
  ])('fails on an unknown id for %s', async (_name, call) => {
    await expect(call(new MockBoardStore())).rejects.toThrow('not found')
  })
})

describe('seed board packing', () => {
  it('fills every row of 12 columns', async () => {
    const widgets: Record<string, string> = {
      'sales-today': 'KpiCard', 'sales-month': 'KpiCard', 'sales-year': 'KpiCard', 'orders-month': 'KpiCard',
      'month-on-month': 'BarChart', 'day-sales': 'LineChart', 'status-split': 'DonutChart', 'month-target': 'GaugeChart',
      'top-customers': 'RankedList', 'top-materials': 'RankedList', 'high-value-sales': 'DataTable',
    }
    const width = (catalogId: string) => {
      const widget = widgets[catalogId]
      return registry.describe().find((entry) => entry.name === widget)!.size.defaultW
    }
    let filled = 0
    for (const widget of (await new MockBoardStore().list())[0].widgets) {
      filled += width(widget.catalogId)
      expect(filled).toBeLessThanOrEqual(12)
      if (filled === 12) filled = 0
    }
    expect(filled).toBe(0)
  })
})

describe('MockBoardStore sharing', () => {
  it('marks a board public and lists the shared boards it was given', async () => {
    const store = new MockBoardStore(undefined, [{ id: 's1', name: 'Plant', owner: 'BOB', widgets: [] }])
    await store.setPublic('board-1', true)
    expect((await store.list())[0].isPublic).toBe(true)
    expect((await store.listShared()).map((board) => board.name)).toEqual(['Plant'])
  })
})
