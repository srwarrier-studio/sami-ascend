import { presets, synapsePalette, workspacePalette } from '../src'

function luminance(hex: string) {
  const channels = [1, 3, 5].map((start) => {
    const value = parseInt(hex.slice(start, start + 2), 16) / 255
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

function contrastWithWhite(hex: string) {
  return 1.05 / (luminance(hex) + 0.05)
}

describe('palette presets', () => {
  it('offers the five presets', () => {
    expect(Object.keys(presets)).toEqual(['teal', 'blue', 'indigo', 'graphite', 'copper'])
  })

  it.each(Object.entries(presets))('%s has ten hex shades for brand, gray and dark', (_name, palette) => {
    for (const key of ['brand', 'gray', 'dark']) {
      expect(palette.colors[key]).toHaveLength(10)
      for (const shade of palette.colors[key]) expect(shade).toMatch(/^#[0-9a-f]{6}$/)
    }
  })

  it.each(Object.entries(presets))('%s filled buttons read at 4.5:1 with white text', (_name, palette) => {
    expect(contrastWithWhite(palette.colors.brand[palette.primaryShade])).toBeGreaterThanOrEqual(4.5)
  })

  it('gives synapse the teal preset and workspace the blue preset', () => {
    expect(synapsePalette).toBe(presets.teal)
    expect(workspacePalette).toBe(presets.blue)
  })
})
