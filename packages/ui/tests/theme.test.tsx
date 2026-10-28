import { cleanup, render, screen } from '@testing-library/react'
import { rem } from '@mantine/core'
import { Button, Card, UiProvider, workspacePalette } from '../src'
import type { RadiusMode } from '../src'
import { createSharedTheme } from '../src/theme'

function renderWith(radius?: RadiusMode) {
  render(
    <UiProvider palette={workspacePalette} radius={radius}>
      <Button>Go</Button>
      <Card data-testid="card">Body</Card>
    </UiProvider>,
  )
  const button = screen.getByRole('button').getAttribute('style') ?? ''
  const card = screen.getByTestId('card').getAttribute('style') ?? ''
  cleanup()
  return { button, card }
}

describe('soft radius', () => {
  it('is the default', () => {
    expect(renderWith()).toEqual(renderWith('soft'))
  })

  it('rounds inputs 6, menus and tiles 12, cards and modals 16, buttons pill', () => {
    const { radius } = createSharedTheme('soft')
    expect(radius).toMatchObject({ sm: rem(6), md: rem(12), lg: rem(16), xl: rem(999) })
  })

  it('gives buttons the pill radius and cards the large radius', () => {
    const { button, card } = renderWith('soft')
    expect(button).toContain('--button-radius: var(--mantine-radius-xl)')
    expect(card).toContain('--paper-radius: var(--mantine-radius-lg)')
  })
})

describe('sharp radius', () => {
  it('still gives buttons and cards their radius keys', () => {
    const { button, card } = renderWith('sharp')
    expect(button).toContain('--button-radius: var(--mantine-radius-xl)')
    expect(card).toContain('--paper-radius: var(--mantine-radius-lg)')
  })

  it('uses 4 for every radius', () => {
    const { radius } = createSharedTheme('sharp')
    expect(Object.values(radius ?? {})).toEqual(Array(5).fill(rem(4)))
  })
})
