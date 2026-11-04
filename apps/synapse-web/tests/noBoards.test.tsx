import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

describe('a user with no boards', () => {
  it('is offered a first board instead of a blank page, and gets it', async () => {
    const store = new MockBoardStore([])
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} boardStore={store} history={createMemoryHistory({ initialEntries: ['/'] })} />
      </UiProvider>,
    )
    expect(await screen.findByText('You have no boards yet')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Create a board' }))
    expect(await screen.findByRole('heading', { name: 'Board 1' })).toBeInTheDocument()
    expect((await store.list()).map((board) => board.name)).toEqual(['Board 1'])
  })
})
