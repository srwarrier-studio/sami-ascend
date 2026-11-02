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
  it('names the main slice in the centre and leaves the others to the legend', () => {
    const { container } = draw()
    const labels = [...container.querySelectorAll('svg text')].map((text) => text.textContent)
    expect(labels).toEqual(['42%', 'Completed'])
  })

  it('has a legend entry per slice with its share', () => {
    draw()
    expect(screen.getByText('Open', { selector: 'li *' })).toBeInTheDocument()
    expect(screen.getByText('In process', { selector: 'li *' })).toBeInTheDocument()
    expect(screen.getByText('Completed', { selector: 'li *' })).toBeInTheDocument()
  })
})

describe('the chart colours', () => {
  it('are defined on the root, so legends and ramps outside the chart area can use them', () => {
    const css = readFileSync('src/charts.css', 'utf8')
    const root = css.slice(css.indexOf(':root'), css.indexOf('}', css.indexOf(':root')))
    for (const step of [1, 2, 3, 4, 5, 6]) expect(root).toContain(`--ts-chart-${step}:`)
  })
})
