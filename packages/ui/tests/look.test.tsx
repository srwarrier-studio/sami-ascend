import { readFileSync } from 'node:fs'
import { render } from '@testing-library/react'
import { UiProvider, presets, synapsePalette, workspacePalette } from '../src'
import type { Look } from '../src'

const lookOf = () => document.documentElement.dataset.look

const renderWith = (look?: Look) =>
  render(
    <UiProvider palette={synapsePalette} look={look}>
      <div />
    </UiProvider>,
  )

describe('the premium look', () => {
  it('is not set by default', () => {
    renderWith()
    expect(lookOf()).toBeUndefined()
  })

  it('sets data-look on the root and removes it on unmount', () => {
    const { unmount } = renderWith('premium')
    expect(lookOf()).toBe('premium')
    unmount()
    expect(lookOf()).toBeUndefined()
  })

  it('only changes the surfaces when the look is premium', () => {
    const css = readFileSync('src/premium.css', 'utf8')
    const selectors = css.split('{').map((part) => part.trim().split('\n').pop() ?? '')
    selectors.filter((selector) => selector.includes('.mantine-') || selector.startsWith(':root[')).forEach((selector) => expect(selector).toContain("data-look='premium'"))
  })

  it('sets the premium surfaces as theme variables only for the premium look', () => {
    const { unmount } = renderWith('premium')
    expect(document.documentElement.innerHTML).toContain('--sami-surface')
    unmount()
    renderWith()
    expect(document.documentElement.innerHTML).not.toContain('--sami-surface:#ffffff')
  })

  it('uses the midnight palette for synapse and gives workspace its own green', () => {
    expect(synapsePalette).toBe(presets.midnight)
    expect(workspacePalette).toBe(presets.green)
  })
})
