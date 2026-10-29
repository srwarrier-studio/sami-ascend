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
