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
  it('shows the sentences and a way into AI Mode', async () => {
    open(new MockCatalogClient())
    const strip = await screen.findByLabelText('Summary')
    expect(within(strip).getByText(/Sales this month are/)).toBeInTheDocument()
    expect(within(strip).getByText(/Acme Ltd moved most/)).toBeInTheDocument()
    expect(within(strip).getByRole('button', { name: 'Ask AI for more' })).toBeInTheDocument()
  })

  it('leads with the first sentence and folds the rest after three', async () => {
    const many = new MockCatalogClient()
    many.summary = async (): Promise<Summary> => ({ currency: 'INR', sentences: ['One.', 'Two.', 'Three.', 'Four.', 'Five.'] })
    open(many)
    const strip = await screen.findByLabelText('Summary')
    expect(within(strip).getByText('Three.')).toBeInTheDocument()
    expect(within(strip).queryByText('Four.')).toBeNull()
    expect(within(strip).getByRole('button', { name: 'Show 2 more' })).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(within(strip).getByRole('button', { name: 'Show 2 more' }))
    expect(within(strip).getByRole('button', { name: 'Show less' })).toHaveAttribute('aria-expanded', 'true')
    expect(within(strip).getByText('Five.')).toBeInTheDocument()
    await userEvent.click(within(strip).getByRole('button', { name: 'Show less' }))
    expect(within(strip).queryByText('Four.')).toBeNull()
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

describe('the overview follows the board', () => {
  it('asks with the catalog ids of the board and asks again when a widget is added', async () => {
    const client = new MockCatalogClient()
    const summary = vi.spyOn(client, 'summary')
    open(client)
    await screen.findByText('Top customers')
    await waitFor(() => expect(summary).toHaveBeenCalledWith(expect.anything(), 'INR', ['sales-month', 'stock-value', 'top-customers']))
    await userEvent.click(screen.getByRole('button', { name: 'Add widget' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add Sales today' }))
    await userEvent.keyboard('{Escape}')
    await userEvent.click(await screen.findByRole('button', { name: 'Done' }))
    await waitFor(() => expect(summary).toHaveBeenLastCalledWith(expect.anything(), 'INR', ['sales-month', 'sales-today', 'stock-value', 'top-customers']))
  })
})
