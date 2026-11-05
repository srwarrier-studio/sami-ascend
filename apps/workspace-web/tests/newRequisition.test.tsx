import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import type { Material, MasterDataClient, Plant } from '../src/api/masterData'
import type { PurchaseRequisitionClient, RequisitionResult } from '../src/api/purchaseRequisitions'

const purchase: User = { userid: 'u1', sap_username: 'ANNA', roles: ['purchase'] }

const created = {
  purchase_requisition: '10000007', description: 'Spares', created_by_user: 'BUTTERFLY', created_on: '2026-11-04',
  total_net_amount: '6250.00', items: [],
}

const bolt: Material = { material: 'RM-1001', description: 'Bolt', unit: 'KG', iso_unit: 'KGM', material_group: 'G', material_type: 'FERT', plants: ['1000'] }
const nut: Material = { material: 'RM-1002', description: 'Nut', unit: 'PC', iso_unit: 'PCE', material_group: 'G', material_type: 'FERT', plants: ['1000'] }
const plantA: Plant = { plant: '1000', name: 'Plant A', company_code: 'INA1' }
const plantB: Plant = { plant: '3000', name: 'Plant B', company_code: 'INA3' }

const clientReturning = (result: RequisitionResult): PurchaseRequisitionClient => ({
  list: vi.fn().mockResolvedValue({ requisitions: [], total: 0 }),
  get: vi.fn().mockResolvedValue(created),
  create: vi.fn().mockResolvedValue(result),
  release: vi.fn(),
})

const masterData = (plants: Plant[] = [plantA], materials: Material[] = [bolt, nut]): MasterDataClient => ({
  plants: vi.fn().mockResolvedValue(plants),
  materials: vi.fn().mockImplementation(async (query: string) => materials.filter((m) => !query || m.material.startsWith(query) || m.description.includes(query))),
  customers: vi.fn().mockResolvedValue([]),
  suppliers: vi.fn().mockResolvedValue([]),
})

const open = (client: PurchaseRequisitionClient, data: MasterDataClient = masterData()) => {
  const auth: AuthClient = { me: vi.fn().mockResolvedValue(purchase), login: vi.fn(), logout: vi.fn() }
  render(
    <UiProvider palette={workspacePalette}>
      <App client={auth} purchaseRequisitions={client} masterData={data} history={createMemoryHistory({ initialEntries: ['/purchase-requisitions/new'] })} />
    </UiProvider>,
  )
}

const ready = () => screen.findByLabelText('Description')
const field = (label: string, index = 0) => screen.getAllByLabelText(label).filter((element) => element.tagName === 'INPUT')[index]

const choose = async (label: string, index: number, option: string) => {
  const input = field(label, index)
  await userEvent.click(input)
  await waitFor(() => expect(document.getElementById(input.getAttribute('aria-controls') ?? '')).not.toBeNull())
  const list = document.getElementById(input.getAttribute('aria-controls') ?? '') as HTMLElement
  await userEvent.click(await within(list).findByText(option))
}

const fillRow = async (index: number, material: string, quantity: string, date = '2026-12-01') => {
  await choose('Material', index, material)
  await userEvent.type(field('Quantity', index), quantity)
  await userEvent.type(field('Delivery date', index), date)
}

describe('entering a requisition', () => {
  it('picks the plant and material from master data and sends the material with its unit', async () => {
    const client = clientReturning({ ok: true, requisition: created })
    const data = masterData([plantA, plantB])
    open(client, data)
    await ready()
    await userEvent.type(field('Description'), 'Spares')
    await choose('Plant', 0, '1000 Plant A')
    await fillRow(0, 'RM-1001 Bolt', '5')
    expect(await screen.findByText('KG')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Add item' }))
    await choose('Plant', 1, '1000 Plant A')
    await fillRow(1, 'RM-1002 Nut', '2', '2026-12-02')
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(client.create).toHaveBeenCalledWith({
      description: 'Spares',
      items: [
        { material: 'RM-1001', plant: '1000', quantity: '5', unit: 'KG', delivery_date: '2026-12-01' },
        { material: 'RM-1002', plant: '1000', quantity: '2', unit: 'PC', delivery_date: '2026-12-02' },
      ],
    })
    expect(vi.mocked(data.materials).mock.calls.every(([, plant]) => plant === '1000')).toBe(true)
    expect(await screen.findByRole('heading', { name: 'Requisition 10000007' })).toBeInTheDocument()
  })

  it('starts on the only plant the user has', async () => {
    open(clientReturning({ ok: true, requisition: created }))
    await ready()
    await waitFor(() => expect(field('Plant')).toHaveValue('1000 Plant A'))
  })

  it('keeps the material dropdown shut until a plant is chosen, and clears the material when the plant changes', async () => {
    open(clientReturning({ ok: true, requisition: created }), masterData([plantA, plantB]))
    await ready()
    expect(field('Material')).toBeDisabled()
    await choose('Plant', 0, '1000 Plant A')
    await choose('Material', 0, 'RM-1001 Bolt')
    expect(field('Material')).toHaveValue('RM-1001 Bolt')
    await choose('Plant', 0, '3000 Plant B')
    await waitFor(() => expect(field('Material')).toHaveValue(''))
  })

  it('asks master data for the typed words, limited to the row\'s plant', async () => {
    const data = masterData()
    open(clientReturning({ ok: true, requisition: created }), data)
    await ready()
    await waitFor(() => expect(field('Material')).toBeEnabled())
    await userEvent.type(field('Material'), 'Nut')
    await waitFor(() => expect(data.materials).toHaveBeenCalledWith('Nut', '1000'))
    expect(await screen.findByText('RM-1002 Nut')).toBeInTheDocument()
  })

  it('puts SAP\'s messages on the right dropdown and field and keeps what was chosen', async () => {
    const details = [
      { code: 'MATERIAL_UNKNOWN', target: 'items/1/material', message: 'Material RM-1002 does not exist in plant 1000.' },
      { code: 'DELIVERY_DATE_IN_PAST', target: 'items/0/delivery_date', message: 'DeliveryDate must not be before today.' },
    ]
    open(clientReturning({ ok: false, kind: 'validation', details }))
    await ready()
    await fillRow(0, 'RM-1001 Bolt', '5')
    await userEvent.click(screen.getByRole('button', { name: 'Add item' }))
    await fillRow(1, 'RM-1002 Nut', '2')
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(await screen.findByText('Material RM-1002 does not exist in plant 1000.')).toBeInTheDocument()
    expect(screen.getByText('DeliveryDate must not be before today.')).toBeInTheDocument()
    expect(field('Material', 0)).toHaveValue('RM-1001 Bolt')
    expect(field('Material', 1)).toHaveValue('RM-1002 Nut')
  })

  it.each([
    [{ ok: false, kind: 'unavailable' }, 'SAP is not reachable. Nothing was saved; try again in a moment.'],
    [{ ok: false, kind: 'notAllowed' }, 'You cannot enter a requisition for that plant.'],
    [{ ok: false, kind: 'failed' }, 'Something went wrong. Nothing was saved; try again.'],
  ] as const)('keeps the form and explains %j', async (result, text) => {
    open(clientReturning(result))
    await ready()
    await fillRow(0, 'RM-1001 Bolt', '5')
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(await screen.findByText(text)).toBeInTheDocument()
    expect(field('Material')).toHaveValue('RM-1001 Bolt')
  })

  it('says so when the plants cannot be loaded and sends nothing', async () => {
    const data = { ...masterData(), plants: vi.fn().mockRejectedValue(new Error('down')) }
    const client = clientReturning({ ok: true, requisition: created })
    open(client, data)
    expect(await screen.findByText('Could not load your plants. Reload the page to try again.')).toBeInTheDocument()
    expect(field('Material')).toBeDisabled()
    expect(client.create).not.toHaveBeenCalled()
  })

  it('removes a row but never the last one', async () => {
    open(clientReturning({ ok: true, requisition: created }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add item' }))
    expect(screen.getAllByLabelText('Material').filter((e) => e.tagName === 'INPUT')).toHaveLength(2)
    await userEvent.click(screen.getAllByRole('button', { name: 'Remove' })[0])
    expect(screen.queryByRole('button', { name: 'Remove' })).not.toBeInTheDocument()
  })

  it('does not send twice while waiting for SAP', async () => {
    const create = vi.fn().mockReturnValue(new Promise(() => {}))
    open({ ...clientReturning({ ok: true, requisition: created }), create })
    await ready()
    await fillRow(0, 'RM-1001 Bolt', '5')
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    await waitFor(() => expect(within(document.body).getByRole('button', { name: 'Create requisition' })).toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: 'Create requisition' }))
    expect(create).toHaveBeenCalledTimes(1)
  })
})
