import { tooltipFor } from '../src/charts'

describe('the chart tooltip', () => {
  const [x, y] = tooltipFor('Day', 'Day sales', 'currency').items

  it('names what the axes show instead of x and y', () => {
    expect(x).toMatchObject({ channel: 'x', label: 'Day' })
    expect(y).toMatchObject({ channel: 'y', label: 'Day sales' })
  })

  it('falls back to Period and Value', () => {
    const [fx, fy] = tooltipFor().items
    expect(fx.label).toBe('Period')
    expect(fy.label).toBe('Value')
  })

  it('formats the value the same way as the rest of the widget', () => {
    expect(y.text?.({ yValue: 211740 })).toMatch(/2,11,740|211,740/)
    expect(y.text?.({ yValue: 'n/a' })).toBe('n/a')
  })
})
