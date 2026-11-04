import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import type { PurchaseRequisitionClient, Requisition, RequisitionItem } from '../src/api/purchaseRequisitions'

const item = (changes: Partial<RequisitionItem> = {}): RequisitionItem => ({
  item: '10', material: 'RM-1001', text: 'Curcumin', plant: '1000', company_code: 'INA1', quantity: '5.000', unit: 'KG',
  net_amount: '6250.00', currency: 'INR', delivery_date: '2026-12-01', release_status: 'released',
  release_status_code: '03', ordered: false, deleted: false, purchase_order: '', ...changes,
})

const requisition = (number: string, ...items: RequisitionItem[]): Requisition => ({
  purchase_requisition: number, description: `Need ${number}`, created_by_user: 'BUTTERFLY', created_on: '2026-11-04',
  total_net_amount: '6250.00', items: items.length ? items : [item()],
})

const mockClient = (changes: Partial<PurchaseRequisitionClient> = {}): PurchaseRequisitionClient => ({
  list: vi.fn().mockResolvedValue({ requisitions: [], total: 0 }),
  get: vi.fn().mockResolvedValue(null),
  create: vi.fn(),
  release: vi.fn(),
  ...changes,
})

const userWith = (...roles: string[]): User => ({ userid: 'u1', sap_username: 'ANNA', roles })

const open = (path: string, user: User, client: PurchaseRequisitionClient) => {
  const auth: AuthClient = { me: vi.fn().mockResolvedValue(user), login: vi.fn(), logout: vi.fn() }
  render(
    <UiProvider palette={workspacePalette}>
      <App client={auth} purchaseRequisitions={client} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )
}

describe('the list', () => {
  it('shows each requisition with its status badge', async () => {
    const client = mockClient({
      list: vi.fn().mockResolvedValue({
        total: 4,
        requisitions: [
          requisition('10000003', item({ release_status: 'not_released', release_status_code: '01' })),
          requisition('10000002', item({ release_status: 'in_release', release_status_code: '02' })),
          requisition('10000001', item()),
          requisition('10000000', item({ ordered: true })),
        ],
      }),
    })
    open('/purchase-requisitions', userWith('purchase'), client)
    const rows = await screen.findAllByRole('row')
    const badge = (row: number) => within(rows[row]).getByText(/^(Not released|In release|Released|Ordered)$/).textContent
    expect([1, 2, 3, 4].map(badge)).toEqual(['Not released', 'In release', 'Released', 'Ordered'])
    expect(screen.getByRole('link', { name: '10000003' })).toHaveAttribute('href', '/purchase-requisitions/10000003')
    expect(client.list).toHaveBeenCalledWith(20, 0)
  })

  it('shows the least advanced item for a mixed requisition', async () => {
    const mixed = requisition('10000000', item(), item({ item: '20', release_status: 'not_released', release_status_code: '01' }))
    open('/purchase-requisitions', userWith('purchase'), mockClient({ list: vi.fn().mockResolvedValue({ total: 1, requisitions: [mixed] }) }))
    expect(await screen.findByText('Not released')).toBeInTheDocument()
  })

  it('pages through the requisitions', async () => {
    const list = vi.fn().mockResolvedValue({ total: 45, requisitions: [requisition('10000000')] })
    open('/purchase-requisitions', userWith('purchase'), mockClient({ list }))
    await userEvent.click(await screen.findByRole('button', { name: '2' }))
    await waitFor(() => expect(list).toHaveBeenLastCalledWith(20, 20))
  })

  it('says so when there are none', async () => {
    open('/purchase-requisitions', userWith('purchase'), mockClient())
    expect(await screen.findByText('No purchase requisitions yet.')).toBeInTheDocument()
  })

  it('says so when SAP cannot be read', async () => {
    open('/purchase-requisitions', userWith('purchase'), mockClient({ list: vi.fn().mockRejectedValue(new Error('x')) }))
    expect(await screen.findByText(/Could not load the requisitions/)).toBeInTheDocument()
  })

  it('offers a purchase user a create button on the page', async () => {
    open('/purchase-requisitions', userWith('purchase'), mockClient())
    await screen.findByText('No purchase requisitions yet.')
    expect(within(screen.getByRole('main')).getByRole('link', { name: 'New requisition' })).toHaveAttribute('href', '/purchase-requisitions/new')
  })

  it('does not offer management the create button', async () => {
    open('/purchase-requisitions', userWith('management'), mockClient())
    await screen.findByText('No purchase requisitions yet.')
    expect(screen.queryByRole('link', { name: 'New requisition' })).not.toBeInTheDocument()
  })
})

const waiting = () => requisition('10000000', item({ release_status: 'not_released', release_status_code: '01' }), item({ item: '20' }))

describe('the detail page', () => {
  it('shows the items with their statuses', async () => {
    open('/purchase-requisitions/10000000', userWith('purchase'), mockClient({ get: vi.fn().mockResolvedValue(waiting()) }))
    expect(await screen.findByRole('heading', { name: 'Requisition 10000000' })).toBeInTheDocument()
    expect(screen.getAllByText('Not released').length).toBeGreaterThan(0)
    expect(screen.getAllByText('5.000 KG')).toHaveLength(2)
    expect(screen.getAllByText('Released').length).toBe(1)
  })

  it('says so for an unknown number', async () => {
    open('/purchase-requisitions/10000099', userWith('purchase'), mockClient())
    expect(await screen.findByText('No such purchase requisition.')).toBeInTheDocument()
  })

  it('says so when SAP cannot be read', async () => {
    open('/purchase-requisitions/10000000', userWith('purchase'), mockClient({ get: vi.fn().mockRejectedValue(new Error('x')) }))
    expect(await screen.findByText('Could not load the requisition.')).toBeInTheDocument()
  })

  it('gives a purchase user no release controls', async () => {
    open('/purchase-requisitions/10000000', userWith('purchase'), mockClient({ get: vi.fn().mockResolvedValue(waiting()) }))
    await screen.findByRole('heading', { name: 'Requisition 10000000' })
    expect(screen.queryByRole('button', { name: /Release/ })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Release code')).not.toBeInTheDocument()
  })

  it('gives management a Release button only for items still to release', async () => {
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()) }))
    await screen.findByLabelText('Release code')
    expect(screen.getByRole('button', { name: 'Release item 10' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Release item 20' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Release all' })).toBeInTheDocument()
  })

  it('releases one item with the code and shows the new status', async () => {
    const after = requisition('10000000', item(), item({ item: '20' }))
    const release = vi.fn().mockResolvedValue({ ok: true, requisition: after })
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()), release }))
    await userEvent.type(await screen.findByLabelText('Release code'), '01')
    await userEvent.click(screen.getByRole('button', { name: 'Release item 10' }))
    expect(release).toHaveBeenCalledWith('10000000', '01', '10')
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Release item 10' })).not.toBeInTheDocument())
    expect(screen.queryAllByText('Not released')).toHaveLength(0)
  })

  it('releases every item with Release all', async () => {
    const release = vi.fn().mockResolvedValue({ ok: true, requisition: waiting() })
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()), release }))
    await userEvent.type(await screen.findByLabelText('Release code'), '01')
    await userEvent.click(screen.getByRole('button', { name: 'Release all' }))
    expect(release).toHaveBeenCalledWith('10000000', '01', undefined)
  })

  it('shows SAP\'s refusal under the button', async () => {
    const details = [{ code: 'RELEASE_REFUSED', target: 'release_code', message: 'Item 10: release code 02 is not the next code in the release strategy.' }]
    const release = vi.fn().mockResolvedValue({ ok: false, kind: 'validation', details })
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()), release }))
    await userEvent.type(await screen.findByLabelText('Release code'), '02')
    await userEvent.click(screen.getByRole('button', { name: 'Release all' }))
    expect(await screen.findByText(/is not the next code/)).toBeInTheDocument()
  })

  it.each([
    [{ ok: false, kind: 'unavailable' }, 'SAP is not reachable. Try again in a moment.'],
    [{ ok: false, kind: 'failed' }, 'Something went wrong. Try again.'],
  ])('explains %j', async (result, text) => {
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()), release: vi.fn().mockResolvedValue(result) }))
    await userEvent.type(await screen.findByLabelText('Release code'), '01')
    await userEvent.click(screen.getByRole('button', { name: 'Release all' }))
    expect(await screen.findByText(text)).toBeInTheDocument()
  })

  it('asks for the code before calling SAP', async () => {
    const release = vi.fn()
    open('/purchase-requisitions/10000000', userWith('management'), mockClient({ get: vi.fn().mockResolvedValue(waiting()), release }))
    await userEvent.click(await screen.findByRole('button', { name: 'Release all' }))
    expect(await screen.findByText('Enter the release code.')).toBeInTheDocument()
    expect(release).not.toHaveBeenCalled()
  })
})
