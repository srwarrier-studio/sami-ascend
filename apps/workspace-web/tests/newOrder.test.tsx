import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import type { MasterDataClient, Material, Partner } from '../src/api/masterData'
import type { CreateResult, SalesOrderClient } from '../src/api/salesOrders'

const user = (roles: string[]): User => ({ userid: 'u1', sap_username: 'ANNA', roles })

const authFor = (u: User | null): AuthClient => ({
  me: vi.fn().mockResolvedValue(u),
  login: vi.fn(),
  logout: vi.fn(),
})

const ordersReturning = (result: CreateResult): SalesOrderClient => ({
  create: vi.fn().mockResolvedValue(result),
  openRequests: vi.fn().mockResolvedValue([]),
})

const steel: Material = { material: 'RM-1001', description: 'Steel rod', unit: 'KG', iso_unit: 'KGM', material_group: 'G', material_type: 'FERT', plants: ['1000'] }
const bolt: Material = { material: 'RM-1002', description: 'Bolt', unit: 'PC', iso_unit: 'PCE', material_group: 'G', material_type: 'FERT', plants: ['1000'] }
const rawResin: Material = { material: 'RAW-2001', description: 'Resin', unit: 'KG', iso_unit: 'KGM', material_group: 'G', material_type: 'ROH', plants: ['1000'] }
const harborline: Partner = { number: '0000100001', name: 'Harborline Nutrition LLC', company_codes: ['INA1'] }
const eurovita: Partner = { number: '0000100002', name: 'Eurovita Ingredients GmbH', company_codes: ['INA1'] }

const masterData = (): MasterDataClient => ({
  plants: vi.fn().mockResolvedValue([]),
  materials: vi.fn().mockImplementation(async (query: string) =>
    [steel, bolt, rawResin].filter((m) => !query || m.material.startsWith(query) || m.description.includes(query)),
  ),
  customers: vi.fn().mockImplementation(async (query: string) =>
    [harborline, eurovita].filter((c) => !query || c.number.startsWith(query) || c.name.includes(query)),
  ),
  suppliers: vi.fn().mockResolvedValue([]),
})

const open = (salesOrders: SalesOrderClient, u: User | null = user(['sales']), data: MasterDataClient = masterData()) =>
  render(
    <UiProvider palette={workspacePalette}>
      <App
        client={authFor(u)}
        salesOrders={salesOrders}
        masterData={data}
        history={createMemoryHistory({ initialEntries: ['/sales-orders/new'] })}
      />
    </UiProvider>,
  )

const created = ordersReturning({ ok: true, salesOrder: '0000012345' })

const field = (label: string, index = 0) => screen.getAllByLabelText(label).filter((element) => element.tagName === 'INPUT')[index]

const choose = async (label: string, index: number, option: string) => {
  const input = field(label, index)
  await userEvent.click(input)
  await waitFor(() => expect(document.getElementById(input.getAttribute('aria-controls') ?? '')).not.toBeNull())
  const list = document.getElementById(input.getAttribute('aria-controls') ?? '') as HTMLElement
  await userEvent.click(await within(list).findByText(option))
}

const fillFirstRow = async () => {
  await choose('Customer', 0, '0000100001 Harborline Nutrition LLC')
  await choose('Material', 0, 'RM-1001 Steel rod')
  await userEvent.type(field('Quantity'), '5')
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
    expect(screen.getAllByLabelText('Material').filter((e) => e.tagName === 'INPUT')).toHaveLength(1)
    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument()
  })

  it('adds and removes item rows', async () => {
    open(created)
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    expect(screen.getAllByLabelText('Material').filter((e) => e.tagName === 'INPUT')).toHaveLength(2)
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0])
    expect(screen.getAllByLabelText('Material').filter((e) => e.tagName === 'INPUT')).toHaveLength(1)
  })
})

describe('picking from master data', () => {
  it('lists customers, searches them and offers only sold materials', async () => {
    const data = masterData()
    open(created, user(['sales']), data)
    await screen.findByLabelText('Order type')
    await userEvent.click(field('Customer'))
    expect(await screen.findByText('0000100002 Eurovita Ingredients GmbH')).toBeInTheDocument()
    await userEvent.type(field('Customer'), 'Harbor')
    await waitFor(() => expect(data.customers).toHaveBeenCalledWith('Harbor'))
    await userEvent.click(field('Material'))
    expect(await screen.findByText('RM-1002 Bolt')).toBeInTheDocument()
    expect(screen.queryByText('RAW-2001 Resin')).not.toBeInTheDocument()
  })

  it('shows the unit of the chosen material beside the quantity', async () => {
    open(created)
    await screen.findByLabelText('Order type')
    await choose('Material', 0, 'RM-1002 Bolt')
    expect(await screen.findByText('PC')).toBeInTheDocument()
  })

  it('says so when a list cannot be loaded', async () => {
    const data = { ...masterData(), customers: vi.fn().mockRejectedValue(new Error('down')) }
    open(created, user(['sales']), data)
    await screen.findByLabelText('Order type')
    await userEvent.click(field('Customer'))
    expect(await screen.findByText('Could not load the list. Try typing again.')).toBeInTheDocument()
  })
})

describe('submit', () => {
  it('sends the chosen customer, its company and the material with its unit, and shows the order number', async () => {
    const orders = ordersReturning({ ok: true, salesOrder: '0000012345' })
    open(orders)
    await screen.findByLabelText('Order type')
    await fillFirstRow()
    await submit()
    expect(await screen.findByText('Sales order 0000012345 created')).toBeInTheDocument()
    expect(orders.create).toHaveBeenCalledWith({
      sales_order_type: 'OR',
      sold_to_party: '0000100001',
      company_code: 'INA1',
      transaction_currency: 'INR',
      requested_delivery_date: null,
      items: [{ material: 'RM-1001', quantity: '5', quantity_unit: 'KG' }],
    })
    expect(field('Customer')).toHaveValue('')
  })

  it('disables the button while the request runs', async () => {
    let finish: (r: CreateResult) => void = () => {}
    const orders: SalesOrderClient = { create: () => new Promise((resolve) => (finish = resolve)), openRequests: async () => [] }
    open(orders)
    await screen.findByLabelText('Order type')
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
      { code: 'MATERIAL_UNKNOWN', target: '_Item/0/Material', message: 'Material does not exist' },
      { code: 'NO_ITEMS', target: '', message: 'Order needs an item' },
    ],
  })

  it('places messages under the customer, the material and the quantity, and clears them on resubmit', async () => {
    open(failing)
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    await submit()
    expect(await screen.findByText('Customer does not exist')).toBeInTheDocument()
    expect(screen.getByText('Material does not exist')).toBeInTheDocument()
    expect(screen.getByText('Order needs an item')).toBeInTheDocument()
    expect(field('Quantity', 1)).toBeInvalid()
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
  ])('shows the message and keeps what was chosen for %j', async (result, text) => {
    open(ordersReturning(result))
    await screen.findByLabelText('Order type')
    await fillFirstRow()
    await submit()
    expect(await screen.findByText(text)).toBeInTheDocument()
    expect(field('Material')).toHaveValue('RM-1001 Steel rod')
    expect(field('Customer')).toHaveValue('0000100001 Harborline Nutrition LLC')
  })
})
