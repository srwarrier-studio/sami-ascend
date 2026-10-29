import { fireEvent, render, screen } from '@testing-library/react'
import { registry, UiProvider, workspacePalette } from '../src'
import { help } from '../src/help'
import { samples } from './samples'

function show(name: string, props: object) {
  return render(<UiProvider palette={workspacePalette}>{registry.render(name, props)}</UiProvider>)
}

const aboutTitle = (props: object) => `About ${(props as { title: string }).title}`

describe('help texts', () => {
  it('cover exactly the registered widgets', () => {
    expect(Object.keys(help).sort()).toEqual(registry.names().sort())
  })

  it.each(Object.keys(help))('%s explains what it shows and how to read it', (name) => {
    expect(help[name as keyof typeof help].shows.length).toBeGreaterThan(10)
    expect(help[name as keyof typeof help].read.length).toBeGreaterThan(10)
  })

  it('are returned by registry.describe() for a model to read', () => {
    for (const widget of registry.describe()) {
      expect(widget.help).toEqual(help[widget.name as keyof typeof help])
    }
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
    expect(screen.getByText(help[name as keyof typeof help].shows)).toBeInTheDocument()
    expect(screen.getByText(help[name as keyof typeof help].read)).toBeInTheDocument()
  })

  it('shows a given info text instead of the default sentence', async () => {
    show('KpiCard', { ...samples.KpiCard, info: 'Net invoiced sales since the 1st.' })
    fireEvent.click(screen.getByRole('button', { name: 'About Today' }))
    expect(await screen.findByText('Net invoiced sales since the 1st.')).toBeInTheDocument()
    expect(screen.queryByText(help.KpiCard.shows)).toBeNull()
    expect(screen.getByText(help.KpiCard.read)).toBeInTheDocument()
  })

  it.each([
    ['LineChart', { data: [{ label: 'Mon', value: 1 }] }],
    ['DataTable', { columns: [{ key: 'a', label: 'A' }], rows: [{ a: 'x' }] }],
  ])('is left out of %s when it has no title', (name, props) => {
    show(name, props)
    expect(screen.queryByRole('button', { name: /^About/ })).toBeNull()
  })
})
