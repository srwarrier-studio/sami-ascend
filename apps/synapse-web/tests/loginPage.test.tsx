import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockSessionClient } from '../src/session/sessionClient'

const open = (motion: 'full' | 'minimal') =>
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient()} ui={{ palette: 'teal', motion }} history={createMemoryHistory({ initialEntries: ['/login'] })} />
    </UiProvider>,
  )

describe('the login page', () => {
  it('shows the brand, the tagline, the form and the network', async () => {
    const { container } = open('full')
    expect(await screen.findByText('Sign in to Sami Synapse')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Sami Synapse' })).toBeInTheDocument()
    expect(screen.getByText('Sense. Connect. Lead.')).toBeInTheDocument()
    expect(container.querySelector('canvas[aria-hidden="true"]')).toHaveAttribute('data-animated', 'true')
  })

  it('does not animate with minimal motion', async () => {
    const { container } = open('minimal')
    await screen.findByText('Sign in to Sami Synapse')
    expect(container.querySelector('canvas')).toHaveAttribute('data-animated', 'false')
  })
})

describe('the Microsoft button', () => {
  it('is there and says it is coming soon', async () => {
    open('full')
    await userEvent.click(await screen.findByRole('button', { name: 'Sign in with Microsoft' }))
    expect(await screen.findByText('Microsoft sign-in is coming soon')).toBeInTheDocument()
  })
})

describe('signing in', () => {
  const fill = async () => {
    await userEvent.type(await screen.findByLabelText(/Work email/), 'manager@mock-sami.com')
    await userEvent.type(screen.getByLabelText(/Password/), 'wrong-password')
  }

  it('says the password is wrong', async () => {
    open('minimal')
    await fill()
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Incorrect email or password')).toBeInTheDocument()
  })

  it('says the service cannot be reached, which is not a wrong password', async () => {
    const client = new MockSessionClient()
    client.login = async () => {
      throw new Error('down')
    }
    render(
      <UiProvider palette={synapsePalette}>
        <App client={client} ui={{ palette: 'teal', motion: 'minimal' }} history={createMemoryHistory({ initialEntries: ['/login'] })} />
      </UiProvider>,
    )
    await fill()
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Cannot reach the sign-in service. Try again in a moment.')).toBeInTheDocument()
    expect(screen.queryByText('Incorrect email or password')).toBeNull()
  })
})
