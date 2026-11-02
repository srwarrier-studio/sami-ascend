import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockSessionClient } from '../src/session/sessionClient'
import type { SessionClient, User } from '../src/session/sessionClient'

const open = (path: string, client: SessionClient) =>
  render(
    <UiProvider palette={synapsePalette}>
      <App client={client} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )

const signIn = async (email: string, password = 'mock') => {
  await userEvent.type(await screen.findByLabelText(/Work email/), email)
  await userEvent.type(screen.getByLabelText(/Password/), password)
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('loading', () => {
  it('shows the splash until me answers', () => {
    const client: SessionClient = { ...new MockSessionClient(), me: () => new Promise<User | null>(() => {}) } as SessionClient
    open('/', client)
    expect(screen.getByText('Sense. Connect. Lead.')).toBeInTheDocument()
  })
})

describe('signed out', () => {
  it('redirects the boards page to login', async () => {
    open('/', new MockSessionClient())
    expect(await screen.findByText('Sign in to Sami Synapse')).toBeInTheDocument()
  })

  it('shows an error on bad credentials and stays', async () => {
    open('/login', new MockSessionClient())
    await signIn('manager@mock-sami.com', 'wrong')
    expect(await screen.findByText('Incorrect email or password')).toBeInTheDocument()
  })

  it('unknown email is rejected', async () => {
    open('/login', new MockSessionClient())
    await signIn('nobody@mock-sami.com')
    expect(await screen.findByText('Incorrect email or password')).toBeInTheDocument()
  })
})

describe('signing in', () => {
  it.each(['manager@mock-sami.com', 'admin@mock-sami.com'])('lets %s reach my boards', async (email) => {
    open('/login', new MockSessionClient())
    await signIn(email)
    expect(await screen.findByRole('heading', { name: 'Sales overview' })).toBeInTheDocument()
  })

  it('sends a sales user to not allowed', async () => {
    open('/login', new MockSessionClient())
    await signIn('sales@mock-sami.com')
    expect(await screen.findByRole('heading', { name: 'Not allowed' })).toBeInTheDocument()
  })
})

describe('signed in', () => {
  it('shows the user in the shell', async () => {
    open('/', new MockSessionClient('manager@mock-sami.com'))
    expect(await screen.findByText('Mock Manager')).toBeInTheDocument()
    expect(screen.getByText('manager@mock-sami.com')).toBeInTheDocument()
  })

  it('redirects login to my boards', async () => {
    open('/login', new MockSessionClient('manager@mock-sami.com'))
    expect(await screen.findByRole('heading', { name: 'Sales overview' })).toBeInTheDocument()
  })

  it('shows page not found for an unknown path', async () => {
    open('/nowhere', new MockSessionClient('manager@mock-sami.com'))
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })

  it('signs out to the login page', async () => {
    open('/', new MockSessionClient('manager@mock-sami.com'))
    await userEvent.click(await screen.findByText('Mock Manager'))
    await userEvent.click(await screen.findByText('Sign out'))
    expect(await screen.findByText('Sign in to Sami Synapse')).toBeInTheDocument()
  })
})

describe('when the login service cannot be reached', () => {
  const unreachable = (): SessionClient => ({
    me: vi.fn().mockRejectedValueOnce(new Error('network')).mockResolvedValue(null),
    login: async () => false,
    logout: async () => undefined,
  })

  it('shows a message with a retry instead of loading forever, and recovers', async () => {
    open('/', unreachable())
    expect(await screen.findByText('Cannot reach the server')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })
})

describe('when the catalog cannot be loaded after sign-in', () => {
  it('shows a message with a retry, and loads the app once it works', async () => {
    const entries = [{ id: 'sales-today', title: 'Sales today', description: 'd', category: 'Sales', widget: 'KpiCard' }]
    const list = vi.fn().mockRejectedValueOnce(new Error('down')).mockResolvedValue(entries)
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={{ list, data: async () => ({}), summary: async () => ({ asOf: '', currency: 'USD', sentences: [] }) }} history={createMemoryHistory({ initialEntries: ['/'] })} />
      </UiProvider>,
    )
    expect(await screen.findByText('Cannot reach the server')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText('Mock Manager')).toBeInTheDocument()
    expect(list).toHaveBeenCalledTimes(2)
  })
})
