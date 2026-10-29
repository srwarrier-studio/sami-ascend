export type SizeName = 'kpi' | 'small' | 'medium' | 'large'

export const sizes: Record<SizeName, { w: number; h: number }> = {
  kpi: { w: 3, h: 2 },
  small: { w: 3, h: 4 },
  medium: { w: 6, h: 4 },
  large: { w: 12, h: 4 },
}

export const sized = (name: SizeName) => {
  const { w, h } = sizes[name]
  return { minW: Math.ceil(w / 2), minH: Math.min(h, 3), defaultW: w, defaultH: h }
}

export const CHART_MIN_HEIGHT = 200
