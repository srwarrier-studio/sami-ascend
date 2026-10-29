import { addWidget, buildWidgets, dropWidget, MAX_WIDGETS, moveWidget, removeWidget, resizeWidget } from '../src/boards/layout'
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

describe('building widgets from ids', () => {
  const catalogIds = (list: { catalogId: string }[]) => list.map((widget) => widget.catalogId)

  it('keeps known ids in order and drops unknown and repeated ones', () => {
    expect(catalogIds(buildWidgets(['top-customers', 'nope', 'day-sales', 'top-customers']))).toEqual(['top-customers', 'day-sales'])
  })

  it('stops at the widget limit', () => {
    expect(buildWidgets(catalog.map((entry) => entry.id))).toHaveLength(MAX_WIDGETS)
  })
})
