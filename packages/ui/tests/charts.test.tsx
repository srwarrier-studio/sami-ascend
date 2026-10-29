import { render } from '@testing-library/react'
import { AreaChart, BarChart, formatCompact, formatValue, HeatmapChart, LineChart, StackedBarChart, UiProvider, workspacePalette } from '../src'

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

describe('AreaChart', () => {
  it('draws one filled area with a line on top and no legend', () => {
    const { container } = show(<AreaChart data={data} />)
    expect(container.querySelectorAll('g.ts-chart__area')).toHaveLength(1)
    expect(container.querySelectorAll('g.ts-chart__line')).toHaveLength(1)
    expect(container.querySelector('.ts-chart__legend')).toBeNull()
  })

  it('shows No data for an empty array', () => {
    expect(show(<AreaChart data={[]} />).getByText('No data')).toBeInTheDocument()
  })
})

const parts = [
  { name: 'Paid', data: data },
  { name: 'Open', data: [{ label: 'Mon', value: 4 }, { label: 'Tue', value: 6 }, { label: 'Wed', value: 5 }] },
]

const barPaths = (container: HTMLElement) => [...container.querySelectorAll('svg g.ts-chart__bar path')].map((bar) => bar.getAttribute('d'))

describe('StackedBarChart', () => {
  it('draws one segment per part per label', () => {
    expect(barPaths(show(<StackedBarChart series={parts} />).container)).toHaveLength(6)
  })

  it('names every part in the legend', () => {
    const legend = show(<StackedBarChart series={parts} />).container.querySelector('.ts-chart__legend')?.textContent
    expect(legend).toContain('Paid')
    expect(legend).toContain('Open')
  })

  it('places parts side by side when grouped', () => {
    const stacked = barPaths(show(<StackedBarChart series={parts} />).container)
    const grouped = barPaths(show(<StackedBarChart series={parts} layout="grouped" />).container)
    expect(grouped).toHaveLength(6)
    expect(grouped).not.toEqual(stacked)
  })

  it('shows No data when every part is empty', () => {
    expect(show(<StackedBarChart series={[{ name: 'Paid', data: [] }]} />).getByText('No data')).toBeInTheDocument()
  })
})

const grid = [
  { row: 'Mon', column: '9', value: 2 },
  { row: 'Mon', column: '10', value: 50 },
  { row: 'Tue', column: '9', value: 80 },
]

const cells = (container: HTMLElement) => [...container.querySelectorAll('g.ts-chart__rect rect')]
const strength = (cell: Element) => Number(/ (\d+)%/.exec(cell.getAttribute('fill') ?? '')?.[1])
const tickLabels = (container: HTMLElement) => [...container.querySelectorAll('[data-ts-key^="x-tick-label"]')].map((label) => label.textContent)

describe('HeatmapChart', () => {
  it('draws one cell per pair and leaves a missing pair empty', () => {
    expect(cells(show(<HeatmapChart cells={grid} />).container)).toHaveLength(3)
  })

  it('shades the lowest cell lightest and the highest cell strongest', () => {
    const strengths = cells(show(<HeatmapChart cells={grid} />).container).map(strength)
    expect(Math.min(...strengths)).toBeLessThan(20)
    expect(Math.max(...strengths)).toBe(100)
  })

  it('shows the low and high values beside the color ramp', () => {
    const { getByText } = show(<HeatmapChart cells={grid} />)
    expect(getByText('2')).toBeInTheDocument()
    expect(getByText('80')).toBeInTheDocument()
  })

  it('draws equal values at one steady shade', () => {
    const flat = grid.map((point) => ({ ...point, value: 3 }))
    expect(new Set(cells(show(<HeatmapChart cells={flat} />).container).map(strength)).size).toBe(1)
  })

  it('keeps columns in the order of the data whatever the values are', () => {
    const descending = [
      { row: 'Mon', column: '9am', value: 90 },
      { row: 'Mon', column: '10am', value: 50 },
      { row: 'Mon', column: '11am', value: 10 },
    ]
    expect(tickLabels(show(<HeatmapChart cells={descending} />).container)).toEqual(['9am', '10am', '11am'])
  })

  it('shows No data for no cells', () => {
    expect(show(<HeatmapChart cells={[]} />).getByText('No data')).toBeInTheDocument()
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
