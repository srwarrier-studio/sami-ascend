import { registry, sizes } from '../src'

describe('standard widget sizes', () => {
  const known = Object.values(sizes).map(({ w, h }) => `${w}x${h}`)

  it('gives every widget one of the named sizes', () => {
    for (const { name, size } of registry.describe()) {
      expect(known, name).toContain(`${size.defaultW}x${size.defaultH}`)
    }
  })

  it('gives the donut and the gauge the same size', () => {
    const size = (name: string) => registry.describe().find((entry) => entry.name === name)!.size
    expect(size('DonutChart')).toEqual(size('GaugeChart'))
  })
})

describe('rows', () => {
  it('pack the playground dashboard into full rows of 12 columns', async () => {
    const { dashboardRows } = await import('../playground/DashboardDemo')
    const width = (name: string) => registry.describe().find((entry) => entry.name === name)!.size.defaultW
    let filled = 0
    for (const widget of dashboardRows.flatMap((row) => row.widgets)) {
      filled += width(widget.name)
      expect(filled).toBeLessThanOrEqual(12)
      if (filled === 12) filled = 0
    }
    expect(filled).toBe(0)
  })
})
