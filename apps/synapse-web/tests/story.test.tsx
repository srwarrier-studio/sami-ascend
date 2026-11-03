import { render, screen, within } from '@testing-library/react'
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
  it('shows the sentences and a way into AI Mode', async () => {
    open(new MockCatalogClient())
    const strip = await screen.findByLabelText('Summary')
    expect(within(strip).getByText(/Sales this month are/)).toBeInTheDocument()
    expect(within(strip).getByText(/Acme Ltd moved most/)).toBeInTheDocument()
    expect(within(strip).getByRole('button', { name: 'Ask AI for more' })).toBeInTheDocument()
  })

  it('draws nothing when there are no sentences or the request fails', async () => {
    const empty = new MockCatalogClient()
    empty.summary = async (): Promise<Summary> => ({ currency: 'INR', sentences: [] })
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

describe('the board update time', () => {
  it('shows when the board last asked for its data, and nothing before the first answer', async () => {
    open(new MockCatalogClient())
    expect(screen.queryByText(/^Updated /)).toBeNull()
    expect(await screen.findByText(/^Updated \d/)).toBeInTheDocument()
  })

  it('has no buttons on the widgets themselves', async () => {
    open(new MockCatalogClient())
    await screen.findByText('Top customers')
    expect(screen.queryByRole('button', { name: /^(Why did|See all)/ })).toBeNull()
  })

  it('opens AI Mode from the summary', async () => {
    open(new MockCatalogClient())
    await userEvent.click(await screen.findByRole('button', { name: 'Ask AI for more' }))
    expect(await screen.findByLabelText('Message')).toBeInTheDocument()
  })
})
