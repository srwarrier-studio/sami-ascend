import { readFileSync } from 'node:fs'
import { render, screen } from '@testing-library/react'
import { DonutChart, UiProvider, synapsePalette } from '../src'

const slices = [
  { label: 'Open', value: 31 },
  { label: 'In process', value: 27 },
  { label: 'Completed', value: 42, tone: 'positive' as const },
]

const draw = () =>
  render(
    <UiProvider palette={synapsePalette}>
      <DonutChart title="Invoice status split" slices={slices} />
    </UiProvider>,
  )

describe('the donut', () => {
  it('shows only the main share inside the ring and leaves the others to the legend', () => {
    const { container } = draw()
    const labels = [...container.querySelectorAll('svg text')].map((text) => text.textContent)
    expect(labels).toEqual(['42%'])
  })

  it('has a legend entry per slice with its share', () => {
    draw()
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('In process')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })
})

describe('the chart colours', () => {
  it('are defined on the root, so legends and ramps outside the chart area can use them', () => {
    const css = readFileSync('src/charts.css', 'utf8')
    const root = css.slice(css.indexOf(':root'), css.indexOf('}', css.indexOf(':root')))
    for (const step of [1, 2, 3, 4, 5, 6]) expect(root).toContain(`--ts-chart-${step}:`)
  })
})
