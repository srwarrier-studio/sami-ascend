import { render, screen } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockSessionClient } from '../src/session/sessionClient'

describe('the app logo', () => {
  it('is the Synapse S in the app bar', async () => {
    const { container } = render(
      <UiProvider palette={synapsePalette}>
        <App client={new MockSessionClient('manager@mock-sami.com')} history={createMemoryHistory({ initialEntries: ['/'] })} />
      </UiProvider>,
    )
    await screen.findByRole('navigation', { name: 'Main' })
    expect(container.querySelector('header svg[viewBox="0 0 800 800"]')).toBeInTheDocument()
  })
})
