export type Cell = { x: number; y: number }

const MIN_RADIUS = 18

export const radiusFor = (width: number) => Math.max(MIN_RADIUS, width / 34)

export const cellsFor = (width: number, height: number): Cell[] => {
  const radius = radiusFor(width)
  const across = Math.sqrt(3) * radius
  const down = 1.5 * radius
  const cells: Cell[] = []
  for (let row = -1; row * down < height + down; row++) {
    for (let col = -1; col * across < width + across; col++) {
      cells.push({ x: col * across + (row % 2 ? across / 2 : 0), y: row * down })
    }
  }
  return cells
}

export const fluxLevel = (u: number, v: number, time: number) => {
  const first = Math.sin((u * 0.82 + v * 0.57) * 9 - time * 0.55)
  const second = Math.sin((u * -0.38 + v * 0.93) * 6.5 + time * 0.34)
  const third = Math.sin((u * 0.95 - v * 0.2) * 3.2 - time * 0.2)
  const level = 0.5 + 0.5 * (0.55 * first + 0.3 * second + 0.15 * third)
  return level * level * level
}

const spread = (index: number, salt: number) => {
  const x = Math.sin(index * 127.1 + salt * 311.7) * 43758.5453
  return x - Math.floor(x)
}

const TWINKLING = 0.3
const LIT_SHARE = 0.3

export const twinkleLevel = (index: number, time: number) => {
  if (spread(index, 1) > TWINKLING) return 0
  const period = 12 + spread(index, 2) * 14
  const place = (((time + spread(index, 3) * period) % period) + period) % period / period
  if (place > LIT_SHARE) return 0
  const pulse = Math.sin((Math.PI * place) / LIT_SHARE)
  return pulse * pulse
}
