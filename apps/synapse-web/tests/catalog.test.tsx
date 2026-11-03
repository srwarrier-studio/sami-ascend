import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, registry, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { CatalogWidget } from '../src/catalog/CatalogWidget'
import { fixtureEntries, fixtures } from '../src/catalog/fixtures'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

describe('catalog fixtures', () => {
  it('have unique ids', () => {
    expect(new Set(fixtureEntries.map((entry) => entry.id)).size).toBe(fixtureEntries.length)
  })

  it.each(fixtures)('$entry.id serves props the registry accepts', async ({ entry }) => {
    expect(registry.names()).toContain(entry.widget)
    const props = await new MockCatalogClient().data(entry.id, null, 'USD')
    const { container } = render(<UiProvider palette={synapsePalette}>{registry.render(entry.widget, props)}</UiProvider>)
    expect(container).not.toHaveTextContent('Cannot show widget')
  })
})

describe('CatalogWidget', () => {
  it('shows a skeleton, then the widget', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget company={null} entry={fixtureEntries[0]} client={new MockCatalogClient()} />
      </UiProvider>,
    )
    expect(screen.getByLabelText('Loading Sales today')).toBeInTheDocument()
    expect(await screen.findByText('Sales today')).toBeInTheDocument()
  })

  it('shows the error when loading fails', async () => {
    const failing = { list: vi.fn(), data: () => Promise.reject(new Error('SAP is not reachable')), summary: () => Promise.reject(new Error('no summary')) }
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget company={null} entry={fixtureEntries[0]} client={failing} />
      </UiProvider>,
    )
    expect(await screen.findByText('SAP is not reachable')).toBeInTheDocument()
  })
})

describe('widget currency', () => {
  const showing = (data: () => Promise<object>) => {
    const spy = vi.fn(data)
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget company="organica" entry={fixtureEntries[0]} client={{ list: vi.fn(), data: spy, summary: () => Promise.reject(new Error('no summary')) }} />
      </UiProvider>,
    )
    return spy
  }
  const money = { title: 'Sales today', value: 5000, valueFormat: 'currency' }

  it('asks for INR and shows the rupee sign while the service names no currency', async () => {
    const data = showing(async () => money)
    expect(await screen.findByText(/^₹/)).toBeInTheDocument()
    expect(data).toHaveBeenCalledWith('sales-today', 'organica', 'INR')
  })

  it('shows the sign of the currency the service names', async () => {
    showing(async () => ({ ...money, currency: 'USD' }))
    expect(await screen.findByText(/^\$/)).toBeInTheDocument()
  })

  it('leaves a widget that is not money alone', async () => {
    showing(async () => ({ title: 'Orders', value: 12, valueFormat: 'number', currency: 'USD' }))
    expect(await screen.findByText('12')).toBeInTheDocument()
    expect(screen.queryByText(/^\$/)).toBeNull()
  })
})

describe('Reports page', () => {
  it('shows a coming soon placeholder', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} history={createMemoryHistory({ initialEntries: ['/reports'] })} />
      </UiProvider>,
    )
    expect(await screen.findByRole('heading', { name: 'Reports' })).toBeInTheDocument()
    expect(screen.getByText('Coming soon')).toBeInTheDocument()
  })

  it('shows one widget error on the board while the others still draw', async () => {
    const mock = new MockCatalogClient()
    const client = { list: () => mock.list(null), data: (id: string) => (id === 'sales-today' ? Promise.reject(new Error('SAP is not reachable')) : mock.data(id, null, 'USD')), summary: () => Promise.reject(new Error('no summary')) }
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={client} history={createMemoryHistory({ initialEntries: ['/'] })} />
      </UiProvider>,
    )
    expect(await screen.findByText('SAP is not reachable')).toBeInTheDocument()
    expect((await screen.findAllByText('Top customers')).length).toBeGreaterThan(0)
  })

  it('sends a signed out user to login', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient()} catalogClient={new MockCatalogClient()} history={createMemoryHistory({ initialEntries: ['/reports'] })} />
      </UiProvider>,
    )
    expect(await screen.findByText('Sign in to Sami Synapse')).toBeInTheDocument()
  })
})
