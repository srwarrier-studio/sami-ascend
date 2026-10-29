import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, registry, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { CatalogWidget } from '../src/catalog/CatalogWidget'
import { catalog } from '../src/catalog/catalog'
import { MockSalesData } from '../src/data/mockSalesData'
import { MockSessionClient } from '../src/session/sessionClient'

const data = new MockSalesData(new Date('2026-10-29T10:00:00Z'))

describe('catalog entries', () => {
  it('have unique ids', () => {
    expect(new Set(catalog.map((entry) => entry.id)).size).toBe(catalog.length)
  })

  it.each(catalog)('$id loads props the registry accepts', async (entry) => {
    expect(registry.names()).toContain(entry.widget)
    const props = await entry.load(data)
    const { container } = render(<UiProvider palette={synapsePalette}>{registry.render(entry.widget, props)}</UiProvider>)
    expect(container).not.toHaveTextContent('Cannot show widget')
  })

  it('give every widget a measure except the table', async () => {
    for (const entry of catalog.filter((entry) => entry.widget !== 'DataTable')) {
      expect(await entry.load(data)).toHaveProperty('measure')
    }
  })

  it('takes KPI deltas from the previous period', async () => {
    const props = (await catalog[1].load(data)) as { delta: number }
    expect(props.delta).toBeCloseTo((3400000 - 3200000) / 3200000)
  })

  it('compares day sales with last month', async () => {
    const props = (await catalog.find((entry) => entry.id === 'day-sales')!.load(data)) as { compare: unknown[] }
    expect(props.compare.length).toBeGreaterThan(0)
  })
})

describe('CatalogWidget', () => {
  it('shows a skeleton, then the widget', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget entry={catalog[0]} data={data} />
      </UiProvider>,
    )
    expect(screen.getByLabelText('Loading Sales today')).toBeInTheDocument()
    expect(await screen.findByText('Sales today')).toBeInTheDocument()
  })

  it('shows the error when loading fails', async () => {
    const failing = { ...data, today: () => Promise.reject(new Error('SAP is not reachable')) } as unknown as MockSalesData
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget entry={catalog[0]} data={failing} />
      </UiProvider>,
    )
    expect(await screen.findByText('SAP is not reachable')).toBeInTheDocument()
  })
})

describe('Widgets page', () => {
  it('lists every catalog title', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} salesData={data} history={createMemoryHistory({ initialEntries: ['/widgets'] })} />
      </UiProvider>,
    )
    expect(await screen.findByRole('heading', { name: 'Widgets' })).toBeInTheDocument()
    for (const title of ['Sales today', 'Sales this month', 'Sales this year', 'Orders this month', 'Month-on-month sales', 'Day sales', 'Recent high-value sales', 'Top customers', 'Top materials', 'Invoice status']) {
      expect((await screen.findAllByText(title)).length).toBeGreaterThan(0)
    }
  })

  it('sends a signed out user to login', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient()} salesData={data} history={createMemoryHistory({ initialEntries: ['/widgets'] })} />
      </UiProvider>,
    )
    expect(await screen.findByText('Sign in to Synapse')).toBeInTheDocument()
  })
})
