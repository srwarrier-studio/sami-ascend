import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'

const sales: User = { userid: 'u1', sap_username: 'ANNA', roles: ['sales'] }

const fakeClient = (user: User | null, loginOk = true): AuthClient => ({
  me: vi.fn().mockResolvedValue(user),
  login: vi.fn().mockImplementation(async () => loginOk),
  logout: vi.fn().mockResolvedValue(undefined),
})

const open = (path: string, client: AuthClient) =>
  render(
    <UiProvider palette={workspacePalette}>
      <App client={client} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )

describe('loading', () => {
  it('shows a loader, not the login page, until me answers', () => {
    const client = { ...fakeClient(null), me: () => new Promise<User | null>(() => {}) }
    open('/', client)
    expect(screen.queryByText('Sign in')).not.toBeInTheDocument()
  })
})

describe('signed out', () => {
  it('redirects home to login', async () => {
    open('/', fakeClient(null))
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })
})

describe('login page', () => {
  it('shows the microsoft failure message', async () => {
    open('/login?error=entra', fakeClient(null))
    expect(await screen.findByText(/Microsoft sign-in failed/)).toBeInTheDocument()
  })

  it('shows an error and stays on bad credentials', async () => {
    open('/login', fakeClient(null, false))
    await userEvent.type(await screen.findByLabelText('Username'), 'anna')
    await userEvent.type(screen.getByLabelText('Password'), 'bad')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Incorrect username or password')).toBeInTheDocument()
  })

  it('lands on home after good credentials', async () => {
    const client = fakeClient(null)
    open('/login', client)
    await userEvent.type(await screen.findByLabelText('Username'), 'anna')
    await userEvent.type(screen.getByLabelText('Password'), 'pw')
    vi.mocked(client.me).mockResolvedValue(sales)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('heading', { name: 'Welcome' })).toBeInTheDocument()
  })
})

describe('signed in', () => {
  it('sends a signed-in user on login to home', async () => {
    open('/login', fakeClient(sales))
    expect(await screen.findByRole('heading', { name: 'Welcome' })).toBeInTheDocument()
  })

  it('shows page not found for an unknown path', async () => {
    open('/nowhere', fakeClient(sales))
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })
})
