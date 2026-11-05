import { readFileSync } from 'node:fs'
import { render } from '@testing-library/react'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from '../src/App'
import { WorkspaceLogo } from '../src/brand/WorkspaceLogo'
import { APP_NAME, TAGLINE } from '../src/config'

describe('the workspace mark', () => {
  it('is hidden from assistive technology and follows the text colour', () => {
    const { container } = render(<WorkspaceLogo size={40} />)
    const svg = container.querySelector('svg')!
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg).toHaveAttribute('width', '40')
    expect(svg.getAttribute('fill')).toBe('currentColor')
  })

  it('gives every mark its own mask so several on one page do not clash', () => {
    const { container } = render(
      <>
        <WorkspaceLogo />
        <WorkspaceLogo />
      </>,
    )
    const ids = [...container.querySelectorAll('mask')].map((mask) => mask.id)
    expect(ids).toHaveLength(2)
    expect(new Set(ids).size).toBe(2)
    container.querySelectorAll('g[mask]').forEach((group, index) => expect(group.getAttribute('mask')).toBe(`url(#${ids[index]})`))
  })
})

describe('the browser tab', () => {
  const page = readFileSync('index.html', 'utf8')

  it('is named after the app and points at the favicon', () => {
    expect(page).toContain(`<title>${APP_NAME}</title>`)
    expect(page).toContain('href="/favicon.svg"')
  })

  it('shows the mark in the workspace green and not the starter icon', () => {
    const icon = readFileSync('public/favicon.svg', 'utf8')
    expect(icon).toContain('#008043')
    expect(icon).toContain('<mask')
    expect(icon).not.toContain('#863bff')
  })
})

describe('the name', () => {
  it('has a tagline', () => {
    expect(TAGLINE).toBe('Work, delivered.')
  })
})

describe('the header', () => {
  it('shows the mark and the name once signed in', async () => {
    const { findAllByText } = render(
      <UiProvider palette={workspacePalette}>
        <App
          client={{ me: vi.fn().mockResolvedValue({ userid: 'u1', sap_username: 'ANNA', roles: ['purchase'] }), login: vi.fn(), logout: vi.fn() }}
          history={createMemoryHistory({ initialEntries: ['/'] })}
        />
      </UiProvider>,
    )
    const [name] = await findAllByText(APP_NAME)
    const near = [name.parentElement, name.parentElement?.parentElement].map((element) => element?.querySelector('svg'))
    expect(near.some(Boolean)).toBe(true)
  })
})
