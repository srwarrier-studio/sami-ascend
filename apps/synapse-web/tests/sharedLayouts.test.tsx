import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const mine = [{ id: 'b1', name: 'Mine', widgets: [{ id: 'w1', catalogId: 'sales-today' }] }]
const shared = [{ id: 's1', name: 'Plant floor', owner: 'BOB', widgets: [{ id: 'x1', catalogId: 'sales-today' }, { id: 'x2', catalogId: 'orders-month' }] }]

const open = (sharedBoards = shared) => {
  const store = new MockBoardStore(structuredClone(mine), sharedBoards)
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} boardStore={store} history={createMemoryHistory({ initialEntries: ['/'] })} />
    </UiProvider>,
  )
  return store
}

const showLayouts = async () => {
  await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
  await userEvent.click(await screen.findByText('Layouts'))
}

describe('shared layouts', () => {
  it('lists shared boards with the Shared tag and the owner', async () => {
    open()
    await showLayouts()
    expect(await screen.findByText('Plant floor')).toBeInTheDocument()
    expect(screen.getByText('Shared')).toBeInTheDocument()
    expect(screen.getByText('By BOB')).toBeInTheDocument()
  })

  it('says so when nothing is shared', async () => {
    open([])
    await showLayouts()
    expect(await screen.findByText('No shared boards yet')).toBeInTheDocument()
  })

  it('copies a shared board into a new private board of the user', async () => {
    const store = open()
    await showLayouts()
    await userEvent.click(await screen.findByRole('button', { name: 'Use Plant floor' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Save' }))
    await waitFor(async () => expect((await store.list()).map((board) => board.name)).toEqual(['Mine', 'Plant floor']))
    expect((await store.list())[1].widgets).toHaveLength(2)
    expect((await store.list())[1].isPublic).toBeUndefined()
  })
})

describe('making a board public', () => {
  it('has a Public switch in Edit mode that saves the flag', async () => {
    const store = open()
    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    await userEvent.click(await screen.findByRole('switch', { name: 'Public' }))
    await waitFor(async () => expect((await store.list())[0].isPublic).toBe(true))
  })
})
