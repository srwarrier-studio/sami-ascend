import { render } from '@testing-library/react'
import { BarChart, formatCompact, formatValue, LineChart, UiProvider, workspacePalette } from '../src'

const data = [
  { label: 'Mon', value: 10 },
  { label: 'Tue', value: 20 },
  { label: 'Wed', value: 15 },
]

function show(element: React.ReactElement) {
  return render(<UiProvider palette={workspacePalette}>{element}</UiProvider>)
}

const previous = [
  { label: 'Mon', value: 8 },
  { label: 'Tue', value: 12 },
  { label: 'Wed', value: 14 },
]

describe('LineChart', () => {
  it('renders an svg with a title', () => {
    const { container, getByText } = show(<LineChart data={data} title="Day sales" />)
    expect(container.querySelector('svg')).not.toBeNull()
    expect(getByText('Day sales')).toBeInTheDocument()
  })

  it('draws one line with an area fill and a marked latest point', () => {
    const { container } = show(<LineChart data={data} />)
    expect(container.querySelectorAll('g.ts-chart__line')).toHaveLength(1)
    expect(container.querySelectorAll('g.ts-chart__area')).toHaveLength(1)
    expect(container.querySelectorAll('g.ts-chart__dot circle')).toHaveLength(1)
  })

  it('has no legend without a compare series', () => {
    expect(show(<LineChart data={data} />).container.querySelector('.ts-chart__legend')).toBeNull()
  })

  it('draws a second line and a legend with a compare series', () => {
    const { container } = show(<LineChart data={data} compare={previous} />)
    expect(container.querySelectorAll('g.ts-chart__line')).toHaveLength(2)
    const legend = container.querySelector('.ts-chart__legend')?.textContent
    expect(legend).toContain('This period')
    expect(legend).toContain('Previous period')
  })

  it('names the series from label and compareLabel', () => {
    const { container } = show(<LineChart data={data} compare={previous} label="October" compareLabel="September" />)
    const legend = container.querySelector('.ts-chart__legend')?.textContent
    expect(legend).toContain('October')
    expect(legend).toContain('September')
  })

  it('shows No data for an empty array', () => {
    const { getByText, container } = show(<LineChart data={[]} />)
    expect(getByText('No data')).toBeInTheDocument()
    expect(container.querySelector('svg')).toBeNull()
  })
})

describe('BarChart', () => {
  it('renders one rounded bar per data point', () => {
    const { container } = show(<BarChart data={data} />)
    expect(container.querySelectorAll('svg g.ts-chart__bar path')).toHaveLength(3)
  })

  it('highlights only the latest bar', () => {
    const { container } = show(<BarChart data={data} />)
    const fills = [...container.querySelectorAll('svg g.ts-chart__bar path')].map((bar) => bar.getAttribute('fill'))
    expect(fills[2]).toBe('var(--ts-chart-1)')
    expect(fills[0]).toContain('color-mix')
    expect(fills[1]).toContain('color-mix')
  })

  it('labels the value axis in compact form', () => {
    const big = [
      { label: 'Sep', value: 2000000 },
      { label: 'Oct', value: 3400000 },
    ]
    const { container } = show(<BarChart data={big} valueFormat="currency" />)
    const ticks = [...container.querySelectorAll('text')].map((text) => text.textContent)
    expect(ticks).toContain('₹2M')
  })

  it('shows No data for an empty array', () => {
    expect(show(<BarChart data={[]} />).getByText('No data')).toBeInTheDocument()
  })
})

describe('formatCompact', () => {
  it('shortens thousands and millions', () => {
    expect(formatCompact(450000)).toBe('450K')
    expect(formatCompact(2000000)).toBe('2M')
    expect(formatCompact(950)).toBe('950')
  })

  it('keeps the rupee sign for currency', () => expect(formatCompact(2000000, 'currency')).toBe('₹2M'))
  it('keeps percent readable', () => expect(formatCompact(0.125, 'percent')).toBe('12.5%'))
})

describe('formatValue', () => {
  it('formats a number', () => expect(formatValue(1234.5)).toBe('1,234.5'))
  it('formats currency in rupees', () => expect(formatValue(1234.5, 'currency')).toBe('₹1,235'))
  it('formats a fraction as percent', () => expect(formatValue(0.125, 'percent')).toBe('12.5%'))
})
