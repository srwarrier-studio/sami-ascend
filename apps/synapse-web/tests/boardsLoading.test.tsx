import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import type { Board } from '../src/boards/boardStore'
import { MockSessionClient } from '../src/session/sessionClient'

describe('while the boards load', () => {
  it('shows a loading skeleton, then the board', async () => {
    let finish: (boards: Board[]) => void = () => undefined
    const store = new MockBoardStore()
    store.list = () => new Promise<Board[]>((resolve) => (finish = resolve))
    render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} boardStore={store} history={createMemoryHistory({ initialEntries: ['/'] })} />
      </UiProvider>,
    )
    expect(await screen.findByRole('status', { name: 'Loading boards' })).toBeInTheDocument()
    finish([{ id: 'b1', name: 'First', widgets: [] }])
    expect(await screen.findByRole('heading', { name: 'First' })).toBeInTheDocument()
    expect(screen.queryByRole('status', { name: 'Loading boards' })).not.toBeInTheDocument()
  })
})
