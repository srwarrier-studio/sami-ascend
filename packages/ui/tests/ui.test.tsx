import { cleanup, render, screen } from '@testing-library/react'
import {
  Alert,
  AppShell,
  Button,
  Card,
  Loader,
  NavLink,
  PasswordInput,
  synapsePalette,
  Text,
  TextInput,
  Title,
  UiProvider,
  workspacePalette,
} from '../src'
import type { Palette } from '../src'

function themeCss(palette: Palette) {
  render(
    <UiProvider palette={palette}>
      <Button>Go</Button>
    </UiProvider>,
  )
  return document.querySelector('style[data-mantine-styles]')?.textContent?.replaceAll(': ', ':') ?? ''
}

describe('UiProvider palettes', () => {
  it('uses the workspace primary color', () => {
    expect(themeCss(workspacePalette)).toContain('--mantine-primary-color-filled:var(--mantine-color-indigo-filled)')
  })

  it('uses the synapse primary color', () => {
    expect(themeCss(synapsePalette)).toContain('--mantine-primary-color-filled:var(--mantine-color-teal-filled)')
  })

  it('shares font, weight and button size across palettes', () => {
    for (const palette of [workspacePalette, synapsePalette]) {
      const css = themeCss(palette)
      expect(css).toContain('--mantine-heading-font-weight:600')
      expect(screen.getByRole('button').getAttribute('style') ?? '').toContain('--button-height-md')
      cleanup()
      expect(css).toContain('--mantine-font-family:system-ui')
    }
  })
})

describe('wrappers render with defaults', () => {
  it('renders every wrapper', () => {
    render(
      <UiProvider palette={workspacePalette}>
        <AppShell>
          <AppShell.Main>
            <TextInput label="User" />
            <PasswordInput label="Password" />
            <Button>Sign in</Button>
            <NavLink label="Sales orders" />
            <Alert>Wrong password</Alert>
            <Loader />
            <Card>
              <Title>Heading</Title>
              <Text>Body</Text>
            </Card>
          </AppShell.Main>
        </AppShell>
      </UiProvider>,
    )
    for (const text of ['Sign in', 'Sales orders', 'Wrong password', 'Heading', 'Body']) {
      expect(screen.getByText(text)).toBeInTheDocument()
    }
    expect(screen.getByLabelText('User')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })
})
