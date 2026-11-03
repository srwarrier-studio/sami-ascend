import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, presets } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'
import { fakeAdmin, user } from './fakes'

const admin: User = { userid: 'me', sap_username: 'BOSS', roles: ['admin'] }

const client = (who: User | null): AuthClient => ({
  me: vi.fn().mockResolvedValue(who),
  login: vi.fn().mockResolvedValue(true),
  logout: vi.fn().mockResolvedValue(undefined),
})

const open = (path: string, who: User | null, api = fakeAdmin()) => {
  render(
    <UiProvider palette={presets.graphite}>
      <App client={client(who)} admin={api} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )
  return api
}

describe('access', () => {
  it('sends a signed-out visitor to sign in', async () => {
    open('/users', null)
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('sends a non-admin to Not allowed', async () => {
    open('/users', { userid: 'x', sap_username: 'ANNA', roles: ['management'] })
    expect(await screen.findByRole('heading', { name: 'Not allowed' })).toBeInTheDocument()
  })

  it('opens the users page for an admin', async () => {
    open('/', admin)
    expect(await screen.findByRole('heading', { name: 'Users' })).toBeInTheDocument()
  })
})

describe('the users table', () => {
  it('shows roles, companies and status, with an Entra badge for users without a password', async () => {
    open('/users', admin, fakeAdmin([user(), user({ userid: 'u2', email: 'eve@sami.com', fullname: 'Eve', has_password: false, disabled: true, roles: ['accounts'] })]))
    expect(await screen.findByText('Bob')).toBeInTheDocument()
    expect(screen.getAllByText('Sami Sabinsa Group Company')).toHaveLength(2)
    expect(screen.getByText('Entra')).toBeInTheDocument()
    const table = within(screen.getByRole('table'))
    expect(table.getByText('Disabled')).toBeInTheDocument()
    expect(table.getByText('Active')).toBeInTheDocument()
  })

  it('searches by name and filters by status', async () => {
    open('/users', admin, fakeAdmin([user(), user({ userid: 'u2', email: 'eve@sami.com', fullname: 'Eve', disabled: true })]))
    await screen.findByText('Bob')
    await userEvent.type(screen.getByLabelText('Search users'), 'eve')
    await waitFor(() => expect(screen.queryByText('Bob')).not.toBeInTheDocument())
    expect(screen.getByText('Eve')).toBeInTheDocument()
  })
})

describe('creating a user', () => {
  it('adds the user and shows the new row', async () => {
    const api = open('/users', admin, fakeAdmin([]))
    await userEvent.click(await screen.findByRole('button', { name: 'New user' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(within(dialog).getByLabelText('Name'), 'Dana')
    await userEvent.type(within(dialog).getByLabelText('Email'), 'dana@sami.com')
    await userEvent.type(within(dialog).getByLabelText('SAP username'), 'DANA')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create user' }))
    await waitFor(() => expect(api.calls).toContain('create dana@sami.com'))
    expect(await screen.findByText('dana@sami.com')).toBeInTheDocument()
  })

  it('says so when the email already exists', async () => {
    open('/users', admin)
    await userEvent.click(await screen.findByRole('button', { name: 'New user' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(within(dialog).getByLabelText('Name'), 'Bob')
    await userEvent.type(within(dialog).getByLabelText('Email'), 'bob@sami.com')
    await userEvent.type(within(dialog).getByLabelText('SAP username'), 'BOB')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create user' }))
    expect(await screen.findByText('A user with this email already exists.')).toBeInTheDocument()
  })
})

describe('editing a user', () => {
  it('saves a changed name', async () => {
    const api = open('/users', admin)
    await userEvent.click(await screen.findByText('Bob'))
    const name = await screen.findByLabelText('Name')
    await userEvent.clear(name)
    await userEvent.type(name, 'Robert')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.calls.some((call) => call.includes('"fullname":"Robert"'))).toBe(true))
  })

  it('asks before disabling and then disables', async () => {
    const api = open('/users', admin)
    await userEvent.click(await screen.findByText('Bob'))
    await userEvent.click(await screen.findByRole('button', { name: 'Disable' }))
    expect(await screen.findByText('Disable Bob?')).toBeInTheDocument()
    expect(api.calls.filter((call) => call.startsWith('update'))).toEqual([])
    await userEvent.click(screen.getByRole('button', { name: 'Yes, disable' }))
    await waitFor(() => expect(api.calls).toContain('update u1 {"disabled":true}'))
  })

  it('shows the last-admin message in words', async () => {
    open('/users', admin, fakeAdmin([user({ userid: 'last', disabled: true, fullname: 'Last One' })]))
    await userEvent.click(await screen.findByText('Last One'))
    await userEvent.click(await screen.findByRole('button', { name: 'Enable' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Yes, enable' }))
    expect(await screen.findByText('At least one active admin is needed.')).toBeInTheDocument()
  })

  it('does not offer to disable yourself', async () => {
    open('/users', admin, fakeAdmin([user({ userid: 'me', fullname: 'Boss', roles: ['admin'] })]))
    await userEvent.click(await screen.findByText('Boss'))
    await screen.findByLabelText('Name')
    expect(screen.queryByRole('button', { name: 'Disable' })).not.toBeInTheDocument()
  })
})
