import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import type { CreateResult, SalesOrderClient } from '../src/api/salesOrders'

const user = (roles: string[]): User => ({ userid: 'u1', sap_username: 'ANNA', roles })

const authFor = (u: User | null): AuthClient => ({
  me: vi.fn().mockResolvedValue(u),
  login: vi.fn(),
  logout: vi.fn(),
})

const ordersReturning = (result: CreateResult): SalesOrderClient => ({
  create: vi.fn().mockResolvedValue(result),
})

const open = (salesOrders: SalesOrderClient, u: User | null = user(['sales'])) =>
  render(
    <UiProvider palette={workspacePalette}>
      <App
        client={authFor(u)}
        salesOrders={salesOrders}
        history={createMemoryHistory({ initialEntries: ['/sales-orders/new'] })}
      />
    </UiProvider>,
  )

const created = ordersReturning({ ok: true, salesOrder: '0000012345' })

const fillFirstRow = async () => {
  await userEvent.type(screen.getByLabelText('Customer number'), ' 0000100001 ')
  await userEvent.type(screen.getByLabelText('Material'), 'RM-1001')
  await userEvent.type(screen.getByLabelText('Quantity'), '5')
  await userEvent.type(screen.getByLabelText('Unit'), 'KG')
}

const submit = () => userEvent.click(screen.getByRole('button', { name: 'Create order' }))

describe('access', () => {
  it('shows the menu entry to sales', async () => {
    open(created)
    expect(await screen.findByRole('link', { name: 'New sales order' })).toBeInTheDocument()
  })

  it('hides the entry and blocks the page for stores', async () => {
    open(created, user(['stores']))
    expect(await screen.findByRole('heading', { name: 'Not allowed' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'New sales order' })).not.toBeInTheDocument()
  })
})

describe('form', () => {
  it('starts with defaults and one item row', async () => {
    open(created)
    expect(await screen.findByLabelText('Order type')).toHaveValue('OR')
    expect(screen.getByLabelText('Currency')).toHaveValue('INR')
    expect(screen.getAllByLabelText('Material')).toHaveLength(1)
    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument()
  })

  it('adds and removes item rows', async () => {
    open(created)
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    expect(screen.getAllByLabelText('Material')).toHaveLength(2)
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0])
    expect(screen.getAllByLabelText('Material')).toHaveLength(1)
  })
})

describe('submit', () => {
  it('sends the typed values and shows the order number', async () => {
    const orders = ordersReturning({ ok: true, salesOrder: '0000012345' })
    open(orders)
    await screen.findByLabelText('Customer number')
    await fillFirstRow()
    await submit()
    expect(await screen.findByText('Sales order 0000012345 created')).toBeInTheDocument()
    expect(orders.create).toHaveBeenCalledWith({
      sales_order_type: 'OR',
      sold_to_party: '0000100001',
      transaction_currency: 'INR',
      requested_delivery_date: null,
      items: [{ material: 'RM-1001', quantity: '5', quantity_unit: 'KG' }],
    })
    expect(screen.getByLabelText('Customer number')).toHaveValue('')
  })

  it('disables the button while the request runs', async () => {
    let finish: (r: CreateResult) => void = () => {}
    const orders: SalesOrderClient = { create: () => new Promise((resolve) => (finish = resolve)) }
    open(orders)
    await screen.findByLabelText('Customer number')
    await submit()
    expect(screen.getByRole('button', { name: 'Create order' })).toBeDisabled()
    finish({ ok: true, salesOrder: '1' })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create order' })).toBeEnabled())
  })
})

describe('validation errors', () => {
  const failing = ordersReturning({
    ok: false,
    kind: 'validation',
    details: [
      { code: 'CUSTOMER_UNKNOWN', target: 'SoldToParty', message: 'Customer does not exist' },
      { code: 'QUANTITY_NOT_POSITIVE', target: '_Item/1/Quantity', message: 'Quantity must be positive' },
      { code: 'NO_ITEMS', target: '', message: 'Order needs an item' },
    ],
  })

  it('places messages on fields and in the alert, and clears them on resubmit', async () => {
    open(failing)
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    await submit()
    expect(await screen.findByText('Customer does not exist')).toBeInTheDocument()
    expect(screen.getByText('Order needs an item')).toBeInTheDocument()
    const secondQuantity = screen.getAllByLabelText('Quantity')[1]
    expect(secondQuantity).toBeInvalid()
    expect(screen.getByText('Quantity must be positive')).toBeInTheDocument()

    vi.mocked(failing.create).mockResolvedValue({ ok: true, salesOrder: '7' })
    await submit()
    await screen.findByText('Sales order 7 created')
    expect(screen.queryByText('Customer does not exist')).not.toBeInTheDocument()
  })
})

describe('other failures', () => {
  it.each([
    [{ ok: false, kind: 'unavailable' } as const, 'SAP is not available. Try again in a moment.'],
    [{ ok: false, kind: 'failed' } as const, 'Something went wrong. Try again.'],
  ])('shows the message and keeps typed values for %j', async (result, text) => {
    open(ordersReturning(result))
    await screen.findByLabelText('Customer number')
    await fillFirstRow()
    await submit()
    expect(await screen.findByText(text)).toBeInTheDocument()
    expect(screen.getByLabelText('Material')).toHaveValue('RM-1001')
  })
})
