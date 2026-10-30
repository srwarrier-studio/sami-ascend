import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockSessionClient } from '../src/session/sessionClient'
import type { SessionClient } from '../src/session/sessionClient'

const open = (path: string, client: SessionClient) =>
  render(
    <UiProvider palette={synapsePalette}>
      <App client={client} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )

const withCompanies = (companies: string[]): SessionClient =>
  ({
    ...new MockSessionClient(),
    me: async () => ({ userid: 'u-test', name: 'Test', email: '', roles: ['management'], companies }),
  }) as SessionClient

beforeEach(() => localStorage.clear())

describe('several companies, none chosen', () => {
  const manager = () => new MockSessionClient('manager@mock-sami.com')

  it('lands on the picker with a card for each company', async () => {
    open('/', manager())
    expect(await screen.findByText('Choose a company')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sami Sabinsa Group Limited/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sami Neutraceuticals Private Limited/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Organica/ })).not.toBeInTheDocument()
  })

  it('redirects another page to the picker', async () => {
    open('/reports', manager())
    expect(await screen.findByText('Choose a company')).toBeInTheDocument()
  })

  it('opens the boards after choosing and remembers the choice', async () => {
    open('/company', manager())
    await userEvent.click(await screen.findByRole('button', { name: /Neutraceuticals/ }))
    expect(await screen.findByText('My boards')).toBeInTheDocument()
    expect(localStorage.getItem('synapse.company.u-manager')).toBe('neutraceuticals')
  })

  it('ignores a stored company the user does not have', async () => {
    localStorage.setItem('synapse.company.u-manager', 'organica')
    open('/', manager())
    expect(await screen.findByText('Choose a company')).toBeInTheDocument()
  })
})

describe('one company', () => {
  it('skips the picker', async () => {
    open('/company', withCompanies(['organica']))
    expect(await screen.findByText('My boards')).toBeInTheDocument()
    expect(screen.queryByText('Choose a company')).not.toBeInTheDocument()
  })
})

describe('no company', () => {
  it('shows the message and blocks the boards', async () => {
    open('/', withCompanies([]))
    expect(await screen.findByText('No company assigned. Ask an administrator.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument()
  })
})

describe('the header', () => {
  it('shows the chosen company with no switch button for one company', async () => {
    open('/', withCompanies(['organica']))
    expect((await screen.findAllByText('Organica Aromatic')).length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: 'Switch company' })).not.toBeInTheDocument()
  })

  it('switches company back through the picker', async () => {
    localStorage.setItem('synapse.company.u-manager', 'sabinsa')
    open('/', new MockSessionClient('manager@mock-sami.com'))
    expect(await screen.findByRole('link', { name: 'Switch company' })).toHaveTextContent('Sami Sabinsa Group Limited')
    await userEvent.click(screen.getByRole('link', { name: 'Switch company' }))
    await userEvent.click(await screen.findByRole('button', { name: /Neutraceuticals/ }))
    expect(await screen.findByRole('link', { name: 'Switch company' })).toHaveTextContent('Sami Neutraceuticals Private Limited')
  })
})
