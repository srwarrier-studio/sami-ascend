import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient } from '../src/api/auth'
import type { CreateResult, OrderRequest, SalesOrderClient } from '../src/api/salesOrders'
import { REFRESH_MS } from '../src/pages/WaitingOrders'

const auth: AuthClient = {
  me: vi.fn().mockResolvedValue({ userid: 'u1', sap_username: 'ANNA', roles: ['sales'] }),
  login: vi.fn(),
  logout: vi.fn(),
}

const waiting = (id: string, status: OrderRequest['status'], attempts = 0, customer = '0000100001'): OrderRequest => ({
  id, status, attempts, created_at: '2026-10-31T09:00:00Z', message: null,
  order: { sales_order_type: 'OR', sold_to_party: customer, transaction_currency: 'INR', requested_delivery_date: null, items: [{ material: 'RM-1001', quantity: '5', quantity_unit: 'KG' }, { material: 'RM-1002', quantity: '1', quantity_unit: 'KG' }] },
})

const client = (create: CreateResult, lists: OrderRequest[][] | Error = [[]]): SalesOrderClient => {
  const openRequests = vi.fn()
  if (lists instanceof Error) openRequests.mockRejectedValue(lists)
  else {
    lists.forEach((list) => openRequests.mockResolvedValueOnce(list))
    openRequests.mockResolvedValue(lists[lists.length - 1])
  }
  return { create: vi.fn().mockResolvedValue(create), openRequests }
}

const open = (salesOrders: SalesOrderClient) =>
  render(
    <UiProvider palette={workspacePalette}>
      <App client={auth} salesOrders={salesOrders} history={createMemoryHistory({ initialEntries: ['/sales-orders/new'] })} />
    </UiProvider>,
  )

const fill = async () => {
  await userEvent.type(await screen.findByLabelText('Customer number'), '0000100001')
  await userEvent.type(screen.getByLabelText('Material'), 'RM-1001')
  await userEvent.type(screen.getByLabelText('Quantity'), '5')
  await userEvent.type(screen.getByLabelText('Unit'), 'KG')
}
const submit = () => userEvent.click(screen.getByRole('button', { name: 'Create order' }))

describe('answers that mean the order is safe', () => {
  it('shows an amber notice, clears the form and reloads the list after a queued answer', async () => {
    const queued = waiting('a', 'queued')
    const orders = client({ ok: false, kind: 'queued', request: queued }, [[], [queued]])
    open(orders)
    await fill()
    await submit()
    expect(await screen.findByText('Saved. SAP could not take the order right now; it will be sent automatically.')).toBeInTheDocument()
    expect(screen.getByLabelText('Customer number')).toHaveValue('')
    expect(screen.getByLabelText('Material')).toHaveValue('')
    expect(await screen.findByText('Will be sent automatically')).toBeInTheDocument()
    expect(orders.openRequests).toHaveBeenCalledTimes(2)
  })

  it('tells the user not to enter an unknown order again, clears the form and lists it', async () => {
    const unknown = waiting('a', 'unknown')
    open(client({ ok: false, kind: 'unknown', request: unknown }, [[], [unknown]]))
    await fill()
    await submit()
    expect(await screen.findByText(/Do not enter it again/)).toBeInTheDocument()
    expect(screen.getByLabelText('Customer number')).toHaveValue('')
    expect(await screen.findByText('Check in SAP')).toBeInTheDocument()
  })
})

describe('an order that was not saved', () => {
  it('keeps the typed values and says nothing was sent', async () => {
    open(client({ ok: false, kind: 'notSaved' }))
    await fill()
    await submit()
    expect(await screen.findByText('The order could not be saved and nothing was sent. Try again.')).toBeInTheDocument()
    expect(screen.getByLabelText('Material')).toHaveValue('RM-1001')
  })
})

describe('the Waiting for SAP panel', () => {
  it('is hidden when nothing waits', async () => {
    open(client({ ok: true, salesOrder: '1' }, [[]]))
    await screen.findByLabelText('Customer number')
    expect(screen.queryByText('Waiting for SAP')).not.toBeInTheDocument()
  })

  it('shows customer, item count, time and the four labels, and tries only when there were some', async () => {
    const list = [waiting('a', 'queued', 2), waiting('b', 'sending', 0, '0000100002'), waiting('c', 'unknown'), waiting('d', 'failed', 8)]
    open(client({ ok: true, salesOrder: '1' }, [list]))
    expect(await screen.findByText('Waiting for SAP')).toBeInTheDocument()
    expect(screen.getByText('Will be sent automatically, tried 2 times')).toBeInTheDocument()
    expect(screen.getByText('Sending')).toBeInTheDocument()
    expect(screen.getByText('Check in SAP')).toBeInTheDocument()
    expect(screen.getByText('Could not be sent, tried 8 times')).toBeInTheDocument()
    expect(screen.getByText('0000100002')).toBeInTheDocument()
    expect(screen.getAllByText('2').length).toBeGreaterThan(0)
  })

  it('says "tried 1 time" in the singular', async () => {
    open(client({ ok: true, salesOrder: '1' }, [[waiting('a', 'queued', 1)]]))
    expect(await screen.findByText('Will be sent automatically, tried 1 time')).toBeInTheDocument()
  })

  it('shows one grey line when it cannot load and leaves the form alone', async () => {
    open(client({ ok: true, salesOrder: '1' }, new Error('down')))
    expect(await screen.findByText('Could not load waiting orders')).toBeInTheDocument()
    expect(screen.getByLabelText('Customer number')).toBeEnabled()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('refreshing', () => {
  beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }))
  afterEach(() => vi.useRealTimers())

  it('reloads every 15 seconds and stops when the page is left', async () => {
    const orders = client({ ok: true, salesOrder: '1' }, [[], [waiting('a', 'queued')]])
    const { unmount } = open(orders)
    await screen.findByLabelText('Customer number')
    expect(orders.openRequests).toHaveBeenCalledTimes(1)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(REFRESH_MS)
    })
    await waitFor(() => expect(orders.openRequests).toHaveBeenCalledTimes(2))
    expect(await screen.findByText('Will be sent automatically')).toBeInTheDocument()
    unmount()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(REFRESH_MS * 3)
    })
    expect(orders.openRequests).toHaveBeenCalledTimes(2)
  })
})
