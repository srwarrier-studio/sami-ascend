import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import type { AuthClient, User } from '../src/api/auth'

const userWith = (roles: string[]): User => ({ userid: 'u1', sap_username: 'ANNA', roles })

const fakeClient = (user: User | null): AuthClient => ({
  me: vi.fn().mockResolvedValue(user),
  login: vi.fn().mockResolvedValue(true),
  logout: vi.fn().mockResolvedValue(undefined),
})

const open = (path: string, user: User | null) =>
  render(
    <UiProvider palette={workspacePalette}>
      <App client={fakeClient(user)} history={createMemoryHistory({ initialEntries: [path] })} />
    </UiProvider>,
  )

describe('menu', () => {
  it('shows a purchase user both requisition entries', async () => {
    open('/', userWith(['purchase']))
    expect(await screen.findByRole('link', { name: 'Purchase requisitions' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'New requisition' })).toBeInTheDocument()
  })

  it('shows management the list only', async () => {
    open('/', userWith(['management']))
    expect(await screen.findByRole('link', { name: 'Purchase requisitions' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'New requisition' })).not.toBeInTheDocument()
  })

  it.each([[['sales']], [['stores']], [['admin']]])('shows %j neither', async (roles) => {
    open('/', userWith(roles))
    await screen.findByRole('heading', { name: 'Welcome' })
    expect(screen.queryByRole('link', { name: 'Purchase requisitions' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'New requisition' })).not.toBeInTheDocument()
  })
})

describe('guards', () => {
  it.each([
    ['/purchase-requisitions/new', ['purchase']],
  ])('lets %s in for %j', async (path, roles) => {
    open(path, userWith(roles))
    expect(await screen.findByRole('heading', { name: 'Coming soon' })).toBeInTheDocument()
  })

  it.each([
    ['/purchase-requisitions', ['sales']],
    ['/purchase-requisitions/new', ['management']],
    ['/purchase-requisitions/10000000', ['stores']],
  ])('sends %s to not allowed for %j', async (path, roles) => {
    open(path, userWith(roles))
    expect(await screen.findByRole('heading', { name: 'Not allowed' })).toBeInTheDocument()
  })

  it('sends a signed-out user to login', async () => {
    open('/purchase-requisitions', null)
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
  })
})
