import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, presets } from '@sami/ui'
import App from '../src/App'
import type { UiSettings } from '../src/router'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const client = new MockSessionClient('manager@mock-sami.com')
const catalogClient = new MockCatalogClient()
const boardStore = new MockBoardStore()

function Root() {
  const [ui, setUi] = useState<UiSettings>({ palette: 'midnight', motion: 'full' })
  return (
    <UiProvider palette={presets[ui.palette]} motion={ui.motion}>
      <App client={client} catalogClient={catalogClient} boardStore={boardStore} ui={ui} onUiChange={setUi} history={createMemoryHistory({ initialEntries: ['/'] })} />
    </UiProvider>
  )
}

describe('the palette in the board settings', () => {
  it('highlights the palette that was picked', async () => {
    render(<Root />)
    await userEvent.click(await screen.findByRole('button', { name: 'Quick settings' }))
    expect(await screen.findByRole('button', { name: 'Midnight', hidden: true })).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(screen.getByText('Copper'))
    expect(await screen.findByRole('button', { name: 'Copper', hidden: true })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Midnight', hidden: true })).toHaveAttribute('aria-pressed', 'false')
  })
})
