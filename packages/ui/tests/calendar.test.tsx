import { render } from '@testing-library/react'
import { CalendarHeatmapChart, dayLabel, registry, UiProvider, workspacePalette } from '../src'

function show(element: React.ReactElement) {
  return render(<UiProvider palette={workspacePalette}>{element}</UiProvider>)
}

function span(from: string, to: string, value = (index: number) => index + 1) {
  const days = []
  for (let time = Date.parse(`${from}T00:00:00Z`), index = 0; time <= Date.parse(`${to}T00:00:00Z`); time += 86400000, index++) {
    days.push({ date: new Date(time).toISOString().slice(0, 10), value: value(index) })
  }
  return days
}

const squares = (container: HTMLElement) => [...container.querySelectorAll('g.ts-chart__rect rect')]
const columns = (container: HTMLElement) => new Set(squares(container).map((square) => square.getAttribute('x'))).size
const topLabels = (container: HTMLElement) =>
  [...container.querySelectorAll('[data-ts-key^="x-tick-label"]')].map((label) => label.textContent).filter(Boolean)
const sideLabels = (container: HTMLElement) =>
  [...container.querySelectorAll('[data-ts-key^="y-tick-label"]')].map((label) => label.textContent).filter(Boolean)

describe('CalendarHeatmapChart days', () => {
  it('draws one cell per day from the first to the last date', () => {
    expect(squares(show(<CalendarHeatmapChart days={span('2026-10-07', '2026-10-20')} />).container)).toHaveLength(14)
  })

  it('draws a faint empty cell for a day with no value', () => {
    const days = [{ date: '2026-10-01', value: 5 }, { date: '2026-10-10', value: 9 }]
    const cells = squares(show(<CalendarHeatmapChart days={days} />).container)
    expect(cells).toHaveLength(10)
    expect(cells.filter((cell) => cell.getAttribute('fill')?.includes('currentColor'))).toHaveLength(8)
  })

  it('lets the last value win for a repeated date', () => {
    const days = [{ date: '2026-10-01', value: 1 }, { date: '2026-10-01', value: 9 }, { date: '2026-10-02', value: 5 }]
    const { getByText } = show(<CalendarHeatmapChart days={days} />)
    expect(getByText('5')).toBeInTheDocument()
    expect(getByText('9')).toBeInTheDocument()
  })

  it('ignores a date that cannot be read', () => {
    const days = [...span('2026-10-05', '2026-10-06'), { date: 'nope', value: 3 }]
    expect(squares(show(<CalendarHeatmapChart days={days} />).container)).toHaveLength(2)
  })

  it('shows No data when there are no days', () => {
    expect(show(<CalendarHeatmapChart days={[]} />).getByText('No data')).toBeInTheDocument()
  })
})

describe('CalendarHeatmapChart weeks', () => {
  it('keeps Monday to Sunday in one column', () => {
    expect(columns(show(<CalendarHeatmapChart days={span('2026-10-05', '2026-10-11')} />).container)).toBe(1)
  })

  it('starts a new column on Monday', () => {
    expect(columns(show(<CalendarHeatmapChart days={span('2026-10-11', '2026-10-17')} />).container)).toBe(2)
  })

  it('labels Monday, Wednesday and Friday down the side in that order', () => {
    expect(sideLabels(show(<CalendarHeatmapChart days={span('2026-10-07', '2026-10-20')} />).container)).toEqual(['Mon', 'Wed', 'Fri'])
  })
})

describe('CalendarHeatmapChart months', () => {
  it('names each month at the week it starts', () => {
    expect(topLabels(show(<CalendarHeatmapChart days={span('2026-09-21', '2026-11-08')} />).container)).toEqual(['Oct', 'Nov'])
  })

  it('also names the first month when it has room', () => {
    expect(topLabels(show(<CalendarHeatmapChart days={span('2026-03-02', '2026-05-31')} />).container)).toEqual(['Mar', 'Apr', 'May'])
  })

  it('shows twelve month names for a full year', () => {
    expect(topLabels(show(<CalendarHeatmapChart days={span('2025-11-03', '2026-10-28')} />).container)).toHaveLength(12)
  })
})

describe('CalendarHeatmapChart legend and shading', () => {
  it('shows the low and high values beside the color ramp', () => {
    const { getByText } = show(<CalendarHeatmapChart days={span('2026-10-05', '2026-10-11', (index) => index * 10 + 2)} />)
    expect(getByText('2')).toBeInTheDocument()
    expect(getByText('62')).toBeInTheDocument()
  })

  it('shades the busiest day strongest', () => {
    const strengths = squares(show(<CalendarHeatmapChart days={span('2026-10-05', '2026-10-11')} />).container).map((cell) =>
      Number(/ (\d+)%/.exec(cell.getAttribute('fill') ?? '')?.[1]),
    )
    expect(Math.max(...strengths)).toBe(100)
    expect(Math.min(...strengths)).toBeLessThan(20)
  })
})

describe('dayLabel', () => {
  it('reads like Wed 14 Oct 2026', () => {
    expect(dayLabel('2026-10-14')).toBe('Wed 14 Oct 2026')
    expect(dayLabel('2026-01-01')).toBe('Thu 1 Jan 2026')
  })
})

describe('registry', () => {
  it('renders a calendar heatmap from days', () => {
    const { container } = show(registry.render('CalendarHeatmapChart', { days: span('2026-10-05', '2026-10-11'), title: 'Sales per day' }))
    expect(squares(container)).toHaveLength(7)
  })

  it('shows the fallback for a date that is not YYYY-MM-DD', () => {
    expect(show(registry.render('CalendarHeatmapChart', { days: [{ date: '14/10/2026', value: 1 }] })).getByText('Cannot show widget CalendarHeatmapChart')).toBeInTheDocument()
  })
})
