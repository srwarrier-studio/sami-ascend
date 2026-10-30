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
    const props = await new MockCatalogClient().data(entry.id)
    const { container } = render(<UiProvider palette={synapsePalette}>{registry.render(entry.widget, props)}</UiProvider>)
    expect(container).not.toHaveTextContent('Cannot show widget')
  })
})

describe('CatalogWidget', () => {
  it('shows a skeleton, then the widget', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget entry={fixtureEntries[0]} client={new MockCatalogClient()} />
      </UiProvider>,
    )
    expect(screen.getByLabelText('Loading Sales today')).toBeInTheDocument()
    expect(await screen.findByText('Sales today')).toBeInTheDocument()
  })

  it('shows the error when loading fails', async () => {
    const failing = { list: vi.fn(), data: () => Promise.reject(new Error('SAP is not reachable')) }
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget entry={fixtureEntries[0]} client={failing} />
      </UiProvider>,
    )
    expect(await screen.findByText('SAP is not reachable')).toBeInTheDocument()
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
    const client = { list: () => mock.list(), data: (id: string) => (id === 'sales-today' ? Promise.reject(new Error('SAP is not reachable')) : mock.data(id)) }
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
