import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, presets } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import { auditCsv } from '../src/csv'
import { entry, fakeAdmin } from './fakes'

const admin: User = { userid: 'me', sap_username: 'BOSS', roles: ['admin'] }
const client: AuthClient = { me: vi.fn().mockResolvedValue(admin), login: vi.fn(), logout: vi.fn() }

const open = (path: string, rows = [entry(1), entry(2, { outcome: 'failed', detail: 'bad_password' })]) => {
  const api = fakeAdmin([], rows)
  render(
    <UiProvider palette={presets.graphite}>
      <App client={client} admin={api} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )
  return api
}

describe('the audit log page', () => {
  it('lists newest first with outcome and detail', async () => {
    open('/audit')
    const table = within(await screen.findByRole('table'))
    await waitFor(() => expect(table.getAllByRole('row')).toHaveLength(3))
    const rows = table.getAllByRole('row')
    expect(within(rows[1]).getByText('failed')).toBeInTheDocument()
    expect(within(rows[1]).getByText('bad_password')).toBeInTheDocument()
    expect(within(rows[2]).getByText('success')).toBeInTheDocument()
  })

  it('keeps filters from the address and sends them', async () => {
    const api = open('/audit?outcome=failed')
    expect(await screen.findByText('bad_password')).toBeInTheDocument()
    expect(screen.getAllByRole('row')).toHaveLength(2)
    expect(api.calls[0]).toContain('"outcome":"failed"')
  })

  it('a quick view narrows the list', async () => {
    const api = open('/audit')
    await screen.findByText('bad_password')
    await userEvent.click(screen.getByRole('button', { name: 'Failed sign-ins' }))
    await waitFor(() => expect(api.calls.some((call) => call.includes('"action":"login.*"') && call.includes('"outcome":"failed"'))).toBe(true))
  })

  it('says so when nothing matches', async () => {
    open('/audit', [])
    expect(await screen.findByText('Nothing in the log matches these filters.')).toBeInTheDocument()
  })

  it('loads more without repeating a row', async () => {
    const rows = Array.from({ length: 60 }, (_, index) => entry(index + 1, { actor: `u${index + 1}@sami.com` }))
    open('/audit', rows)
    await screen.findByText('u60@sami.com')
    expect(screen.getAllByRole('row')).toHaveLength(51)
    await userEvent.click(screen.getByRole('button', { name: 'Load more' }))
    await waitFor(() => expect(screen.getAllByRole('row')).toHaveLength(61))
    expect(screen.queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
    expect(screen.getAllByText('u1@sami.com')).toHaveLength(1)
  })

  it('refresh asks again', async () => {
    const api = open('/audit')
    await screen.findByText('bad_password')
    await userEvent.click(screen.getByRole('button', { name: 'Refresh' }))
    await waitFor(() => expect(api.calls.filter((call) => call.startsWith('audit')).length).toBeGreaterThan(1))
  })
})

describe('the CSV export', () => {
  it('has a header, quotes cells and defuses formulas', () => {
    const csv = auditCsv([entry(1, { actor: '=cmd|x', detail: 'say "hi", ok' })])
    expect(csv.split('\r\n')[0]).toBe('at,actor,action,target,outcome,detail')
    expect(csv).toContain('"\'=cmd|x"')
    expect(csv).toContain('"say ""hi"", ok"')
  })

  it('never contains more than the six columns', () => {
    expect(auditCsv([entry(1)]).split('\r\n')[1].split('","')).toHaveLength(6)
  })
})
