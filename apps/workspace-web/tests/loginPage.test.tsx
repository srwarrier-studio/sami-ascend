import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import { entraLoginUrl } from '../src/api/auth'
import type { AuthClient } from '../src/api/auth'

const client = (login: AuthClient['login']): AuthClient => ({
  me: vi.fn().mockResolvedValue(null),
  login,
  logout: vi.fn().mockResolvedValue(undefined),
})

const open = (login: AuthClient['login'] = vi.fn().mockResolvedValue(false), path = '/login') => {
  render(
    <UiProvider palette={workspacePalette}>
      <App client={client(login)} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )
  return login
}

const signIn = async (email: string, password: string) => {
  await screen.findByRole('heading', { name: 'Sami Workspace' })
  fireEvent.change(screen.getByLabelText(/work email/i), { target: { value: email } })
  fireEvent.change(screen.getByLabelText(/^password/i), { target: { value: password } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('the sign-in page', () => {
  it('shows the brand, the tagline and the card', async () => {
    open()
    expect(await screen.findByRole('heading', { name: 'Sami Workspace' })).toBeInTheDocument()
    expect(screen.getByText('Work, delivered.')).toBeInTheDocument()
    expect(screen.getByText('Sign in to Sami Workspace')).toBeInTheDocument()
  })

  it('sends the typed email and password', async () => {
    const login = open()
    await signIn('anna@sami.test', 'a long secret')
    await waitFor(() => expect(login).toHaveBeenCalledWith('anna@sami.test', 'a long secret'))
  })

  it('says when the email or password is wrong', async () => {
    open()
    await signIn('anna@sami.test', 'nope')
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })

  it('says when the sign-in service cannot be reached', async () => {
    open(vi.fn().mockRejectedValue(new Error('down')))
    await signIn('anna@sami.test', 'secret')
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the sign-in service')
  })

  it('offers the Microsoft sign-in at the Entra address', async () => {
    open()
    expect(await screen.findByRole('link', { name: 'Sign in with Microsoft' })).toHaveAttribute('href', entraLoginUrl)
  })

  it('shows the Microsoft failure when Entra sent the user back with an error', async () => {
    open(undefined, '/login?error=entra')
    expect(await screen.findByRole('alert')).toHaveTextContent('Microsoft sign-in failed')
  })
})
