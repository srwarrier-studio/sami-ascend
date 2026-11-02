import { cleanup, render } from '@testing-library/react'
import { DonutChart, GaugeChart, KpiCard, UiProvider, formatDelta, workspacePalette } from '../src'

function show(element: React.ReactElement) {
  return render(<UiProvider palette={workspacePalette}>{element}</UiProvider>)
}

const status = [
  { label: 'Paid', value: 58, tone: 'positive' as const },
  { label: 'Open', value: 27 },
  { label: 'Overdue', value: 15, tone: 'negative' as const },
]

const centerText = (container: HTMLElement) => [...container.querySelectorAll('svg text')].map((text) => text.textContent)
const arcs = (container: HTMLElement) => container.querySelectorAll('svg path')

describe('DonutChart', () => {
  it('draws one arc per slice', () => {
    expect(arcs(show(<DonutChart slices={status} />).container)).toHaveLength(3)
  })

  it('shows the main share in the center', () => {
    expect(centerText(show(<DonutChart slices={status} />).container)).toContain('58%')
  })

  it('lists every slice with its share in a legend', () => {
    const { getByText } = show(<DonutChart slices={status} />)
    for (const text of ['Paid', 'Open', 'Overdue', '58%', '27%', '15%']) expect(getByText(text, { selector: 'li *' })).toBeInTheDocument()
  })

  it('paints toned slices with status colors and the rest from the palette', () => {
    const { container } = show(<DonutChart slices={status} />)
    const dots = [...container.querySelectorAll('li span[data-color]')].map((dot) => dot.getAttribute('data-color'))
    expect(dots).toEqual(['positive', '2', 'negative'])
  })

  it('shows the title', () => {
    expect(show(<DonutChart slices={status} title="Invoice status" />).getByText('Invoice status')).toBeInTheDocument()
  })

  it.each([[[]], [[{ label: 'Paid', value: 0 }]]])('shows No data when the total is not positive', (slices) => {
    expect(show(<DonutChart slices={slices} />).getByText('No data')).toBeInTheDocument()
  })
})

describe('GaugeChart', () => {
  it('shows the percent of target in the center', () => {
    expect(centerText(show(<GaugeChart value={72} target={100} />).container)).toContain('72%')
  })

  it('shows the value against the target', () => {
    expect(show(<GaugeChart value={3400000} target={5000000} valueFormat="currency" />).getByText('₹34,00,000 of ₹50,00,000')).toBeInTheDocument()
  })

  it('shows the real percent above 100 and keeps drawing a full ring', () => {
    const { container } = show(<GaugeChart value={120} target={100} />)
    expect(centerText(container)).toContain('120%')
    expect(arcs(container)).toHaveLength(2)
  })

  it('shows 0% for no progress', () => {
    expect(centerText(show(<GaugeChart value={0} target={100} />).container)).toContain('0%')
  })

  it('shows No data when the target is not positive', () => {
    expect(show(<GaugeChart value={5} target={0} />).getByText('No data')).toBeInTheDocument()
  })
})

describe('KpiCard', () => {
  it('shows a rising change with a plus sign', () => {
    const { getByText } = show(<KpiCard title="Sales" value={10} delta={0.062} />)
    expect(getByText('+6.2%')).toBeInTheDocument()
  })

  it('shows a falling change with a minus sign', () => {
    expect(show(<KpiCard title="Sales" value={10} delta={-0.014} />).getByText('-1.4%')).toBeInTheDocument()
  })

  it('draws a sparkline only when a trend is given', () => {
    expect(show(<KpiCard title="Sales" value={10} trend={[1, 2, 3]} />).container.querySelector('.sami-spark')).not.toBeNull()
    expect(show(<KpiCard title="Sales" value={10} />).container.querySelector('.sami-spark')).toBeNull()
  })

  it('skips the sparkline for a single value', () => {
    expect(show(<KpiCard title="Sales" value={10} trend={[1]} />).container.querySelector('.sami-spark')).toBeNull()
  })

  it('draws a flat trend without breaking', () => {
    expect(show(<KpiCard title="Sales" value={10} trend={[5, 5, 5]} />).container.querySelector('.sami-spark-line')).not.toBeNull()
  })
})

describe('formatDelta', () => {
  it('signs a change', () => {
    expect(formatDelta(0.05)).toBe('+5%')
    expect(formatDelta(-0.125)).toBe('-12.5%')
    expect(formatDelta(0)).toBe('0%')
  })
})

describe('DonutChart with many slices', () => {
  const many = Array.from({ length: 9 }, (_, index) => ({ label: `Part ${index + 1}`, value: 10 - index }))

  it('keeps the five largest and groups the rest as Other', () => {
    const { container } = show(<DonutChart slices={many} />)
    const names = [...container.querySelectorAll('li')].map((item) => item.textContent)
    expect(names).toHaveLength(6)
    expect(names[5]).toMatch(/^Other/)
    expect(arcs(container)).toHaveLength(6)
  })

  it('shows up to six slices as they are', () => {
    const { container } = show(<DonutChart slices={many.slice(0, 6)} />)
    expect(container.querySelectorAll('li')).toHaveLength(6)
    expect(container.textContent).not.toContain('Other')
  })
})

describe('KpiCard story', () => {
  const colourOf = (delta: number, partial = false) => {
    cleanup()
    const { getByText } = show(<KpiCard title="Sales" value={10} delta={delta} partial={partial} />)
    return getByText(/%$/).getAttribute('style') ?? ''
  }

  it('paints only a fall worse than 10% as needing attention', () => {
    expect(colourOf(0.37)).not.toContain('--sami-negative')
    expect(colourOf(0.05)).not.toContain('--sami-negative')
    expect(colourOf(-0.05)).not.toContain('--sami-negative')
    expect(colourOf(-0.12)).toContain('--sami-negative')
  })

  it('never paints a rise green', () => {
    expect(colourOf(0.37)).not.toContain('--sami-positive')
  })

  it('keeps a partial period grey however far it fell and shows its note', () => {
    expect(colourOf(-0.583, true)).not.toContain('--sami-negative')
    expect(show(<KpiCard title="Sales" value={10} partial note="2 of 30 days so far" />).getByText('2 of 30 days so far')).toBeInTheDocument()
  })

  it('shows the time the figure was read, and nothing without it', () => {
    expect(show(<KpiCard title="Sales" value={10} asOf="2026-11-02T17:11:00+00:00" />).getByText(/^as of \d/)).toBeInTheDocument()
    cleanup()
    expect(show(<KpiCard title="Orders" value={1} />).queryByText(/as of/)).toBeNull()
    cleanup()
    expect(show(<KpiCard title="Sales" value={1} note="2 of 30 days so far" asOf="2026-11-02T17:11:00+00:00" />).getByText(/^2 of 30 days so far \u00b7 as of \d/)).toBeInTheDocument()
  })

  it('shows the gauge reading time too', () => {
    expect(show(<GaugeChart value={1} target={2} asOf="2026-11-02T17:11:00+00:00" />).getByText(/^as of \d/)).toBeInTheDocument()
  })
})
