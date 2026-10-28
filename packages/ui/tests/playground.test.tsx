import { cleanup, render, screen } from '@testing-library/react'
import { UiProvider, presets } from '../src'
import type { PresetName } from '../src'
import { KitchenSink } from '../playground/KitchenSink'
import { ThemeLab, defaultLab } from '../playground/ThemeLab'

const sections = [
  'Tokens',
  'Buttons',
  'Inputs',
  'Data display',
  'Overlays',
  'Feedback',
  'Notifications',
  'Navigation',
  'Widgets and charts',
]

const settings = (Object.keys(presets) as PresetName[]).flatMap((palette) =>
  (['soft', 'sharp'] as const).flatMap((radius) => (['full', 'minimal'] as const).map((motion) => [palette, radius, motion] as const)),
)

describe('playground kitchen sink', () => {
  it.each(settings)('renders every section with the %s palette, %s radius and %s motion', (palette, radius, motion) => {
    render(
      <UiProvider palette={presets[palette]} radius={radius} motion={motion}>
        <KitchenSink />
      </UiProvider>,
    )
    const titles = screen.getAllByRole('heading', { level: 4 }).map((heading) => heading.textContent)
    const seen = sections.filter((section) => titles.includes(section))
    expect(seen).toEqual(sections)
    cleanup()
  })
})

describe('theme lab', () => {
  it('starts with the teal palette, soft radius, full motion and top layout', () => {
    expect(defaultLab).toEqual({ palette: 'teal', radius: 'soft', motion: 'full', layout: 'top' })
  })

  it('offers every preset and the other switches', () => {
    render(
      <UiProvider palette={presets.teal}>
        <ThemeLab lab={defaultLab} onChange={() => undefined} />
      </UiProvider>,
    )
    for (const label of ['Teal', 'Blue', 'Indigo', 'Graphite', 'Copper', 'Soft', 'Sharp', 'Full', 'Minimal', 'Top', 'Side']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })
})
