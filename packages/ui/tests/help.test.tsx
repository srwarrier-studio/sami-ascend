import { fireEvent, render, screen } from '@testing-library/react'
import { registry, UiProvider, workspacePalette } from '../src'
import { DEFAULT_MEASURE, help, helpText } from '../src/help'
import type { WidgetName } from '../src/help'
import { samples } from './samples'

function show(name: string, props: object) {
  return render(<UiProvider palette={workspacePalette}>{registry.render(name, props)}</UiProvider>)
}

const aboutTitle = (props: object) => `About ${(props as { title: string }).title}`
const names = Object.keys(help) as WidgetName[]
const measured = names.filter((name) => name !== 'DataTable')

describe('help texts', () => {
  it('cover exactly the registered widgets', () => {
    expect([...names].sort()).toEqual(registry.names().sort())
  })

  it.each(names)('%s explains what it shows and how to read it', (name) => {
    expect(helpText(name).shows.length).toBeGreaterThan(10)
    expect(helpText(name).read.length).toBeGreaterThan(10)
  })

  it.each(measured)('%s names the measure it was given', (name) => {
    const text = helpText(name, 'sales')
    expect(`${text.shows} ${text.read}`).toContain('sales')
    expect(`${text.shows} ${text.read}`).not.toContain(DEFAULT_MEASURE)
  })

  it.each(measured)('%s falls back to the value without a measure', (name) => {
    const text = helpText(name)
    expect(`${text.shows} ${text.read}`).toContain(DEFAULT_MEASURE)
  })

  it('starts a sentence with a capital letter when the measure leads it', () => {
    expect(helpText('CalendarHeatmapChart', 'sales').shows).toBe('Sales on each day of the period.')
    expect(helpText('CalendarHeatmapChart').shows).toBe('The value on each day of the period.')
  })

  it('tells the calendar reader what the strength of a square means', () => {
    const { read } = helpText('CalendarHeatmapChart', 'sales')
    expect(read).toContain('Colour strength follows sales')
    expect(read).toContain('Each square is one day')
  })

  it('is returned by registry.describe() for a model to read', () => {
    for (const widget of registry.describe()) {
      expect(widget.help).toEqual(helpText(widget.name as WidgetName))
    }
  })

  it('leaves the measure to a widget prop that the registry accepts', () => {
    const calendar = registry.describe().find((widget) => widget.name === 'CalendarHeatmapChart')
    expect(JSON.stringify(calendar?.schema)).toContain('"measure"')
  })
})

describe('info button', () => {
  it.each(Object.entries(samples))('%s has an About button named after its title', (name, props) => {
    show(name, props)
    expect(screen.getByRole('button', { name: aboutTitle(props) })).toBeInTheDocument()
  })

  it.each(Object.entries(samples))('%s opens what it shows and how to read it', async (name, props) => {
    show(name, props)
    fireEvent.click(screen.getByRole('button', { name: aboutTitle(props) }))
    expect(await screen.findByText('What it shows')).toBeInTheDocument()
    expect(screen.getByText('How to read it')).toBeInTheDocument()
    expect(screen.getByText(helpText(name as WidgetName).shows)).toBeInTheDocument()
    expect(screen.getByText(helpText(name as WidgetName).read)).toBeInTheDocument()
  })

  it('explains the chart in terms of the given measure', async () => {
    show('CalendarHeatmapChart', { ...samples.CalendarHeatmapChart, measure: 'sales' })
    fireEvent.click(screen.getByRole('button', { name: 'About Sales per day' }))
    expect(await screen.findByText('Sales on each day of the period.')).toBeInTheDocument()
    expect(screen.getByText(/Colour strength follows sales/)).toBeInTheDocument()
  })

  it('shows a given info text instead of the default sentence but keeps how to read it', async () => {
    show('KpiCard', { ...samples.KpiCard, info: 'Net invoiced sales since the 1st.', measure: 'sales' })
    fireEvent.click(screen.getByRole('button', { name: 'About Today' }))
    expect(await screen.findByText('Net invoiced sales since the 1st.')).toBeInTheDocument()
    expect(screen.queryByText(helpText('KpiCard', 'sales').shows)).toBeNull()
    expect(screen.getByText(helpText('KpiCard', 'sales').read)).toBeInTheDocument()
  })

  it.each([
    ['LineChart', { data: [{ label: 'Mon', value: 1 }] }],
    ['DataTable', { columns: [{ key: 'a', label: 'A' }], rows: [{ a: 'x' }] }],
  ])('is left out of %s when it has no title', (name, props) => {
    show(name, props)
    expect(screen.queryByRole('button', { name: /^About/ })).toBeNull()
  })
})
