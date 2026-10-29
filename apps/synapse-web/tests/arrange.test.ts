import { arrange } from '@sami/ui'

const shape = (item: { w: number; h: number }) => item
const w = (name: string, width: number, h = 4) => ({ name, w: width, h })
const names = (list: { name: string }[]) => list.map((item) => item.name)

describe('auto arrange', () => {
  it('pulls a later widget up to fill a row', () => {
    const list = [w('a', 6), w('b', 12), w('c', 6)]
    expect(names(arrange(list, shape))).toEqual(['a', 'c', 'b'])
  })

  it('keeps the order when rows already fill', () => {
    const list = [w('a', 3), w('b', 3), w('c', 6), w('d', 12)]
    expect(names(arrange(list, shape))).toEqual(['a', 'b', 'c', 'd'])
  })

  it('only fills a row with widgets of the same height', () => {
    const list = [w('kpi', 3, 2), w('big', 3), w('kpi2', 3, 2)]
    expect(names(arrange(list, shape))).toEqual(['kpi', 'kpi2', 'big'])
  })
})
