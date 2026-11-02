import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'
import type { Summary } from '../src/catalog/catalogClient'

const store = () =>
  new MockBoardStore([{ id: 'b1', name: 'Sales', widgets: [{ id: 'w1', catalogId: 'sales-month' }, { id: 'w2', catalogId: 'top-customers' }, { id: 'w3', catalogId: 'stock-value' }] }])

const open = (client: MockCatalogClient) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={client} boardStore={store()} history={createMemoryHistory({ initialEntries: ['/'] })} />
    </UiProvider>,
  )
}

describe('the summary strip', () => {
  it('shows the sentences and when they were read', async () => {
    open(new MockCatalogClient())
    const strip = await screen.findByLabelText('Summary')
    expect(within(strip).getByText(/Sales this month are/)).toBeInTheDocument()
    expect(within(strip).getByText(/Acme Ltd moved most/)).toBeInTheDocument()
    expect(within(strip).getByText(/^as of \d/)).toBeInTheDocument()
  })

  it('draws nothing when there are no sentences or the request fails', async () => {
    const empty = new MockCatalogClient()
    empty.summary = async (): Promise<Summary> => ({ asOf: '', currency: 'USD', sentences: [] })
    open(empty)
    await screen.findByText('Top customers')
    expect(screen.queryByLabelText('Summary')).toBeNull()
  })

  it('draws nothing when the request fails', async () => {
    const broken = new MockCatalogClient()
    broken.summary = () => Promise.reject(new Error('down'))
    open(broken)
    await screen.findByText('Top customers')
    expect(screen.queryByLabelText('Summary')).toBeNull()
  })
})

describe('opening a widget into the answer', () => {
  it('offers Why? on the sales cards and See all on the rankings, and nothing on other widgets', async () => {
    open(new MockCatalogClient())
    expect(await screen.findByRole('button', { name: 'Why did Sales this month change?' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'See all Top customers' })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /^(Why did|See all)/ })).toHaveLength(2)
  })

  it('asks for twenty rows when See all is pressed', async () => {
    const client = new MockCatalogClient()
    const data = vi.spyOn(client, 'data')
    open(client)
    await userEvent.click(await screen.findByRole('button', { name: 'See all Top customers' }))
    await waitFor(() => expect(data).toHaveBeenCalledWith('top-customers', expect.anything(), 'USD', 20))
  })

  it('hides both while the board is edited', async () => {
    open(new MockCatalogClient())
    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    expect(screen.queryByRole('button', { name: /^Why did/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /^See all/ })).toBeNull()
  })

  it('opens AI Mode with the why question', async () => {
    open(new MockCatalogClient())
    await userEvent.click(await screen.findByRole('button', { name: 'Why did Sales this month change?' }))
    expect(await screen.findByText('Why did sales change last month?')).toBeInTheDocument()
  })
})
