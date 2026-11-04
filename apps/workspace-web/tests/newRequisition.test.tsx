import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import type { PurchaseRequisitionClient, RequisitionResult } from '../src/api/purchaseRequisitions'

const purchase: User = { userid: 'u1', sap_username: 'ANNA', roles: ['purchase'] }

const created = {
  purchase_requisition: '10000007', description: 'Spares', created_by_user: 'BUTTERFLY', created_on: '2026-11-04',
  total_net_amount: '6250.00', items: [],
}

const clientReturning = (result: RequisitionResult): PurchaseRequisitionClient => ({
  list: vi.fn().mockResolvedValue({ requisitions: [], total: 0 }),
  get: vi.fn().mockResolvedValue(created),
  create: vi.fn().mockResolvedValue(result),
  release: vi.fn(),
})

const open = (client: PurchaseRequisitionClient) => {
  const auth: AuthClient = { me: vi.fn().mockResolvedValue(purchase), login: vi.fn(), logout: vi.fn() }
  render(
    <UiProvider palette={workspacePalette}>
      <App client={auth} purchaseRequisitions={client} history={createMemoryHistory({ initialEntries: ['/purchase-requisitions/new'] })} />
    </UiProvider>,
  )
}

const ready = () => screen.findByLabelText('Description')

const fillRow = async (index: number, values: { material: string; plant: string; quantity: string; unit: string; date: string }) => {
  await userEvent.type(screen.getAllByLabelText('Material')[index], values.material)
  await userEvent.type(screen.getAllByLabelText('Plant')[index], values.plant)
  await userEvent.type(screen.getAllByLabelText('Quantity')[index], values.quantity)
  await userEvent.type(screen.getAllByLabelText('Unit')[index], values.unit)
  await userEvent.type(screen.getAllByLabelText('Delivery date')[index], values.date)
}

const row = { material: 'RM-1001', plant: '1000', quantity: '5', unit: 'KG', date: '2026-12-01' }

describe('entering a requisition', () => {
  it('sends the filled rows and opens the new requisition', async () => {
    const client = clientReturning({ ok: true, requisition: created })
    open(client)
    await userEvent.type(await screen.findByLabelText('Description'), 'Spares')
    await fillRow(0, row)
    await userEvent.click(screen.getByRole('button', { name: 'Add item' }))
    await fillRow(1, { ...row, material: 'RM-1002', quantity: '2' })
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(client.create).toHaveBeenCalledWith({
      description: 'Spares',
      items: [
        { material: 'RM-1001', plant: '1000', quantity: '5', unit: 'KG', delivery_date: '2026-12-01' },
        { material: 'RM-1002', plant: '1000', quantity: '2', unit: 'KG', delivery_date: '2026-12-01' },
      ],
    })
    expect(await screen.findByRole('heading', { name: 'Requisition 10000007' })).toBeInTheDocument()
  })

  it('puts SAP\'s messages on the right row and keeps what was typed', async () => {
    const details = [
      { code: 'MATERIAL_UNKNOWN', target: 'items/1/material', message: 'Material NOPE does not exist.' },
      { code: 'DELIVERY_DATE_IN_PAST', target: 'items/0/delivery_date', message: 'DeliveryDate must not be before today.' },
    ]
    open(clientReturning({ ok: false, kind: 'validation', details }))
    await ready()
    await fillRow(0, row)
    await userEvent.click(screen.getByRole('button', { name: 'Add item' }))
    await fillRow(1, { ...row, material: 'NOPE' })
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(await screen.findByText('Material NOPE does not exist.')).toBeInTheDocument()
    expect(screen.getByText('DeliveryDate must not be before today.')).toBeInTheDocument()
    expect(screen.getAllByLabelText('Material')[1]).toHaveValue('NOPE')
    expect(screen.getAllByLabelText('Material')[0]).toHaveValue('RM-1001')
    expect(screen.queryByRole('heading', { name: /Requisition 1/ })).not.toBeInTheDocument()
  })

  it.each([
    [{ ok: false, kind: 'unavailable' }, 'SAP is not reachable. Nothing was saved; try again in a moment.'],
    [{ ok: false, kind: 'notAllowed' }, 'You cannot enter a requisition for that plant.'],
    [{ ok: false, kind: 'failed' }, 'Something went wrong. Nothing was saved; try again.'],
  ] as const)('keeps the form and explains %j', async (result, text) => {
    open(clientReturning(result))
    await ready()
    await fillRow(0, row)
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(await screen.findByText(text)).toBeInTheDocument()
    expect(screen.getByLabelText('Material')).toHaveValue('RM-1001')
  })

  it('removes a row but never the last one', async () => {
    open(clientReturning({ ok: true, requisition: created }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    expect(screen.getAllByLabelText('Material')).toHaveLength(2)
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0])
    expect(screen.getAllByLabelText('Material')).toHaveLength(1)
    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument()
  })

  it('does not send twice while waiting for SAP', async () => {
    const create = vi.fn().mockReturnValue(new Promise(() => {}))
    open({ ...clientReturning({ ok: true, requisition: created }), create })
    await ready()
    await fillRow(0, row)
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create requisition' })).toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(create).toHaveBeenCalledTimes(1)
  })
})
