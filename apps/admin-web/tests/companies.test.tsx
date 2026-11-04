import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, presets } from '@sami/ui'
import App from '../src/App'
import type { AuthClient } from '../src/api/auth'
import { fakeAdmin, user } from './fakes'

describe('the companies selector', () => {
  it('offers the companies and saves the chosen one', async () => {
    const api = fakeAdmin([user({ companies: [] })])
    const client: AuthClient = { me: vi.fn().mockResolvedValue({ userid: 'me', sap_username: 'BOSS', roles: ['admin'] }), login: vi.fn(), logout: vi.fn() }
    render(
      <UiProvider palette={presets.graphite}>
        <App client={client} admin={api} history={createMemoryHistory({ initialEntries: ['/users'] })} />
      </UiProvider>,
    )
    await userEvent.click(await screen.findByText('Bob'))
    await userEvent.click(await within(await screen.findByRole('dialog')).findByLabelText('Companies'))
    await userEvent.click(await screen.findByRole('checkbox', { name: 'Organica Aromatic' }))
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() => expect(api.calls.some((call) => call.includes('"companies":["organica"]'))).toBe(true))
  })
})
