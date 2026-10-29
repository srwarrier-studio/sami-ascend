import { cleanup, render, screen } from '@testing-library/react'
import { presets, registry, UiProvider } from '../src'
import type { PresetName } from '../src'
import { dashboardRows } from '../playground/DashboardDemo'
import { samples } from './samples'

const forbidden = /colou?r|style|class|width|height|font|size|stroke|fill|radius|opacity|px|theme/i

function propertyNames(schema: unknown): string[] {
  if (Array.isArray(schema)) return schema.flatMap(propertyNames)
  if (schema === null || typeof schema !== 'object') return []
  return Object.entries(schema).flatMap(([key, value]) => (key === 'properties' ? Object.keys(value as object).concat(propertyNames(value)) : propertyNames(value)))
}

describe('widgets take data only', () => {
  it.each(registry.describe())('$name has no style prop', ({ schema }) => {
    expect(propertyNames(schema).filter((name) => forbidden.test(name))).toEqual([])
  })

  it('catches a style prop when one is added', () => {
    expect(propertyNames({ properties: { data: {}, color: {} } }).filter((name) => forbidden.test(name))).toEqual(['color'])
  })
})

const settings = (Object.keys(presets) as PresetName[]).flatMap((palette) =>
  (['soft', 'sharp'] as const).flatMap((radius) => (['full', 'minimal'] as const).map((motion) => [palette, radius, motion] as const)),
)

describe('every widget under every setting', () => {
  it.each(settings)('renders with the %s palette, %s radius and %s motion', (palette, radius, motion) => {
    render(
      <UiProvider palette={presets[palette]} radius={radius} motion={motion}>
        {Object.entries(samples).map(([name, props]) => (
          <div key={name}>{registry.render(name, props)}</div>
        ))}
      </UiProvider>,
    )
    expect(screen.queryByText(/Cannot show widget/)).toBeNull()
    expect(screen.getAllByRole('button', { name: /^About / })).toHaveLength(Object.keys(samples).length)
    cleanup()
  })
})

describe('the Charts page', () => {
  it('shows every registered widget', () => {
    const shown = new Set(dashboardRows.flatMap((row) => row.widgets.map((widget) => widget.name)))
    expect([...shown].sort()).toEqual(registry.names().sort())
  })

  it('only uses props the registry accepts', () => {
    for (const row of dashboardRows) {
      for (const widget of row.widgets) {
        render(<UiProvider palette={presets.teal}>{registry.render(widget.name, widget.props)}</UiProvider>)
        expect(screen.queryByText(`Cannot show widget ${widget.name}`)).toBeNull()
        cleanup()
      }
    }
  })
})
