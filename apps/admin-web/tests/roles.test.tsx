import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, presets } from '@sami/ui'
import App from '../src/App'
import type { AuthClient } from '../src/api/auth'
import { fakeAdmin } from './fakes'

describe('the roles checkboxes', () => {
  it('shows what each role opens and saves the chosen ones', async () => {
    const api = fakeAdmin([])
    const client: AuthClient = { me: vi.fn().mockResolvedValue({ userid: 'me', sap_username: 'BOSS', roles: ['admin'] }), login: vi.fn(), logout: vi.fn() }
    render(
      <UiProvider palette={presets.graphite}>
        <App client={client} admin={api} history={createMemoryHistory({ initialEntries: ['/users'] })} />
      </UiProvider>,
    )
    await userEvent.click(await screen.findByRole('button', { name: 'New user' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Synapse production widgets.')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('checkbox', { name: /^production/ }))
    await userEvent.click(within(dialog).getByRole('checkbox', { name: /^accounts/ }))
    await userEvent.type(within(dialog).getByLabelText('Name'), 'Dana')
    await userEvent.type(within(dialog).getByLabelText('Email'), 'dana@sami.com')
    await userEvent.type(within(dialog).getByLabelText('SAP username'), 'DANA')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create user' }))
    await waitFor(() => expect(api.calls).toContain('create dana@sami.com'))
    expect((await api.users('dana'))[0].roles).toEqual(['production', 'accounts'])
  })
})

describe('the master data role', () => {
  it('is offered with its help text and can be given', async () => {
    const api = fakeAdmin([])
    const client: AuthClient = { me: vi.fn().mockResolvedValue({ userid: 'me', sap_username: 'BOSS', roles: ['admin'] }), login: vi.fn(), logout: vi.fn() }
    render(
      <UiProvider palette={presets.graphite}>
        <App client={client} admin={api} history={createMemoryHistory({ initialEntries: ['/users'] })} />
      </UiProvider>,
    )
    await userEvent.click(await screen.findByRole('button', { name: 'New user' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Checks and creates customer, supplier and material records in workspace.')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('checkbox', { name: /^master-data/ }))
    await userEvent.type(within(dialog).getByLabelText('Name'), 'Mira')
    await userEvent.type(within(dialog).getByLabelText('Email'), 'mira@sami.com')
    await userEvent.type(within(dialog).getByLabelText('SAP username'), 'MIRA')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Create user' }))
    await waitFor(() => expect(api.calls).toContain('create mira@sami.com'))
    expect((await api.users('mira'))[0].roles).toEqual(['master-data'])
  })
})
