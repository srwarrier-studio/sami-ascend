import { addWidget, applyOps, dropWidget, MAX_WIDGETS, moveWidget, removeWidget, resizeWidget } from '../src/boards/layout'
import { catalog } from '../src/catalog/catalog'

const widgets = [
  { id: 'a', catalogId: 'x' },
  { id: 'b', catalogId: 'y' },
  { id: 'c', catalogId: 'z' },
]
const ids = (list: { id: string }[]) => list.map((widget) => widget.id)

describe('board layout', () => {
  it('adds a widget at the end with a new id', () => {
    const next = addWidget(widgets, 'top-customers')
    expect(next).toHaveLength(4)
    expect(next[3].catalogId).toBe('top-customers')
    expect(ids(widgets)).toEqual(['a', 'b', 'c'])
  })

  it('removes a widget', () => {
    expect(ids(removeWidget(widgets, 'b'))).toEqual(['a', 'c'])
  })

  it('moves a widget later and earlier', () => {
    expect(ids(moveWidget(widgets, 'a', 1))).toEqual(['b', 'a', 'c'])
    expect(ids(moveWidget(widgets, 'c', -1))).toEqual(['a', 'c', 'b'])
  })

  it('does not move past either end', () => {
    expect(moveWidget(widgets, 'a', -1)).toBe(widgets)
    expect(moveWidget(widgets, 'c', 1)).toBe(widgets)
  })

  it('drops a widget onto another', () => {
    expect(ids(dropWidget(widgets, 'a', 'c'))).toEqual(['b', 'c', 'a'])
    expect(ids(dropWidget(widgets, 'c', 'a'))).toEqual(['c', 'a', 'b'])
  })

  it('ignores a drop onto itself or an unknown id', () => {
    expect(dropWidget(widgets, 'a', 'a')).toBe(widgets)
    expect(dropWidget(widgets, 'a', 'nope')).toBe(widgets)
  })
})

describe('resizing a widget', () => {
  const allowed: ('medium' | 'large')[] = ['medium', 'large']

  it('moves to the next allowed size and wraps to the first', () => {
    const large = resizeWidget(widgets, 'a', allowed)
    expect(large[0].size).toBe('large')
    expect(resizeWidget(large, 'a', allowed)[0].size).toBe('medium')
  })

  it('leaves other widgets alone', () => {
    expect(resizeWidget(widgets, 'a', allowed)[1]).toBe(widgets[1])
  })
})

describe('applying canvas ops', () => {
  const start = [{ id: 'a', catalogId: 'sales-today' }]

  it('adds a known widget once', () => {
    const next = applyOps(start, [{ type: 'add', catalogId: 'top-customers' }, { type: 'add', catalogId: 'top-customers' }])
    expect(next.map((widget) => widget.catalogId)).toEqual(['sales-today', 'top-customers'])
  })

  it('ignores an unknown widget and a duplicate of one already there', () => {
    expect(applyOps(start, [{ type: 'add', catalogId: 'nope' }, { type: 'add', catalogId: 'sales-today' }])).toBe(start)
  })

  it('removes a widget by id', () => {
    expect(applyOps(start, [{ type: 'remove', widgetId: 'a' }])).toEqual([])
  })

  it('replaces everything with the given widgets, skipping unknown and repeated ones', () => {
    const next = applyOps(start, [{ type: 'replaceAll', catalogIds: ['top-customers', 'nope', 'top-customers', 'day-sales'] }])
    expect(next.map((widget) => widget.catalogId)).toEqual(['top-customers', 'day-sales'])
  })

  it('resizes to an allowed size and ignores a size the widget does not allow', () => {
    const chart = [{ id: 'c', catalogId: 'month-on-month' }]
    expect(applyOps(chart, [{ type: 'resize', widgetId: 'c', size: 'large' }])[0].size).toBe('large')
    expect(applyOps(chart, [{ type: 'resize', widgetId: 'c', size: 'kpi' }])).toBe(chart)
  })

  it('stops at the widget limit', () => {
    const ids = catalog.map((entry) => entry.id)
    expect(applyOps([], [{ type: 'replaceAll', catalogIds: ids }])).toHaveLength(MAX_WIDGETS)
  })
})
