import { render } from '@testing-library/react'
import { BarChart, UiProvider, registry, synapsePalette } from '../src'

const months = ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
const sales = months.map((label, index) => ({ label, value: index === 8 ? 7570000 : index === 9 ? 6480000 : 9000000 }))

const draw = (props: Partial<Parameters<typeof BarChart>[0]> = {}, data = sales) =>
  render(
    <UiProvider palette={synapsePalette}>
      <BarChart title="Month-on-month sales" data={data} valueFormat="currency" {...props} />
    </UiProvider>,
  )

const labels = (container: HTMLElement) => [...container.querySelectorAll('svg text')].map((node) => node.textContent)

describe('value labels on bars', () => {
  it('shows each bar value in whole lakhs, without the rupee sign, so the labels stay narrow', () => {
    const found = labels(draw().container)
    expect(found).toEqual(expect.arrayContaining(['76L', '65L', '90L']))
    expect(found).not.toContain('₹76L')
  })

  it('keeps the rupee sign on the axis', () => {
    expect(labels(draw().container).some((text) => /^₹\d+L$/.test(text ?? ''))).toBe(true)
  })

  it('shows one label per bar', () => {
    const bar = draw({ valueFormat: 'number' }, [{ label: 'A', value: 1200 }, { label: 'B', value: 3400 }, { label: 'C', value: 560 }])
    expect(labels(bar.container)).toEqual(expect.arrayContaining(['1K', '3K', '560']))
  })

  it('can be turned off', () => {
    expect(labels(draw({ valueLabels: false }).container)).not.toContain('76L')
  })

  it('is left out when there are too many bars to read', () => {
    const many = Array.from({ length: 20 }, (_, index) => ({ label: `L${index}`, value: 4200000 }))
    expect(labels(draw({}, many).container)).not.toContain('42L')
  })

  it('is accepted by the widget registry so a backend can switch it off', () => {
    expect(registry.validate('BarChart', { data: sales, valueLabels: false })).toBe(true)
    expect(registry.validate('BarChart', { data: sales, valueLabels: 'no' })).toBe(false)
  })
})
