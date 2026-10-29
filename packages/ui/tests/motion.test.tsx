import { readFileSync } from 'node:fs'
import { render } from '@testing-library/react'
import { UiProvider, workspacePalette } from '../src'
import type { MotionMode } from '../src'

const motionOf = () => document.documentElement.dataset.motion

function renderWith(motion?: MotionMode) {
  return render(
    <UiProvider palette={workspacePalette} motion={motion}>
      <div />
    </UiProvider>,
  )
}

describe('motion mode', () => {
  it('is full by default', () => {
    renderWith()
    expect(motionOf()).toBe('full')
  })

  it('is minimal when asked', () => {
    renderWith('minimal')
    expect(motionOf()).toBe('minimal')
  })

  it('follows the prop when it changes', () => {
    const view = renderWith('full')
    view.rerender(
      <UiProvider palette={workspacePalette} motion="minimal">
        <div />
      </UiProvider>,
    )
    expect(motionOf()).toBe('minimal')
  })

  it('is removed when the provider unmounts', () => {
    renderWith('minimal').unmount()
    expect(motionOf()).toBeUndefined()
  })
})

describe('motion stylesheet', () => {
  const css = readFileSync('src/motion.css', 'utf8')

  it('plays animations only in full mode', () => {
    expect(css).toContain(":root[data-motion='full'] .sami-chart svg")
  })

  it('turns animations off in minimal mode and for reduced motion', () => {
    expect(css).toContain(":root[data-motion='minimal'] *")
    expect(css).toContain('@media (prefers-reduced-motion: reduce)')
    expect(css.match(/animation: none !important/g)).toHaveLength(2)
  })
})
