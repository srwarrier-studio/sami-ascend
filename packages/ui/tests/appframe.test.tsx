import { fireEvent, render, screen, within } from '@testing-library/react'
import { AppFrame, HouseIcon, SquaresFourIcon, UiProvider, synapsePalette } from '../src'

type Layout = 'top' | 'side'

function renderFrame(layout: Layout, onSignOut = () => undefined, onSelect = () => undefined) {
  render(
    <UiProvider palette={synapsePalette}>
      <AppFrame
        layout={layout}
        brand={{ name: 'Synapse', subtitle: 'Management' }}
        user={{ name: 'Mock Manager', email: 'manager@mock-sami.com' }}
        onSignOut={onSignOut}
        notifications={2}
        navGroups={[
          [
            { key: 'boards', label: 'My boards', icon: SquaresFourIcon, active: true, onSelect },
            { key: 'home', label: 'Home', icon: HouseIcon, badge: 3 },
          ],
        ]}
      >
        <p>Page body</p>
      </AppFrame>
    </UiProvider>,
  )
}

describe.each<Layout>(['top', 'side'])('AppFrame %s layout', (layout) => {
  it('shows brand, user, page body and the notification count', () => {
    renderFrame(layout)
    expect(screen.getByText('Synapse')).toBeInTheDocument()
    expect(screen.getByText('Mock Manager')).toBeInTheDocument()
    expect(screen.getByText('manager@mock-sami.com')).toBeInTheDocument()
    expect(screen.getByText('Page body')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('lists the nav items, marks the active one and shows the badge', () => {
    renderFrame(layout)
    const nav = within(screen.getByRole('navigation', { name: 'Main' }))
    expect(nav.getByText('My boards').closest('[data-active]')).not.toBeNull()
    expect(nav.getByText('Home').closest('[data-active]')).toBeNull()
    expect(nav.getByText('3')).toBeInTheDocument()
  })

  it('calls onSelect when a nav item is clicked', () => {
    const onSelect = vi.fn()
    renderFrame(layout, undefined, onSelect)
    fireEvent.click(screen.getByText('My boards'))
    expect(onSelect).toHaveBeenCalledOnce()
  })

  it('signs out from the user menu', async () => {
    const onSignOut = vi.fn()
    renderFrame(layout, onSignOut)
    fireEvent.click(screen.getByText('Mock Manager'))
    fireEvent.click(await screen.findByText('Sign out'))
    expect(onSignOut).toHaveBeenCalledOnce()
  })

  it('has a light and dark toggle', () => {
    renderFrame(layout)
    expect(screen.getByLabelText('Dark theme')).toBeInTheDocument()
  })
})

describe('AppFrame differences', () => {
  it('shows the brand subtitle in the side layout only', () => {
    renderFrame('side')
    expect(screen.getByText('Management')).toBeInTheDocument()
  })

  it('leaves the subtitle out of the top layout', () => {
    renderFrame('top')
    expect(screen.queryByText('Management')).toBeNull()
  })

  it('is the side layout by default', () => {
    render(
      <UiProvider palette={synapsePalette}>
        <AppFrame brand={{ name: 'Synapse', subtitle: 'Management' }} user={{ name: 'A', email: 'a@b.c' }} onSignOut={() => undefined} navGroups={[]}>
          <p>Body</p>
        </AppFrame>
      </UiProvider>,
    )
    expect(screen.getByText('Management')).toBeInTheDocument()
  })
})
