export type Point = { x: number; y: number }
export type Neuron = { soma: Point; trunks: string; twigs: string; tips: Point[]; axon: string | null; axonLength: number; terminal: Point | null }

export const SOMA_RADIUS = 8
const TERMINAL_GAP = 26

export const somas: Point[] = [
  [110, 140], [300, 90], [480, 200], [660, 110], [560, 380], [330, 330], [130, 430],
].map(([x, y]) => ({ x, y }))

const random = (seed: number) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296
  return seed / 4294967296
}

const at = (from: Point, angle: number, length: number): Point => ({
  x: from.x + Math.cos(angle) * length,
  y: from.y + Math.sin(angle) * length,
})

const fixed = (point: Point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`

const grow = (from: Point, angle: number, length: number, depth: number, rnd: () => number, out: { trunks: string[]; twigs: string[]; tips: Point[] }) => {
  const end = at(from, angle + (rnd() - 0.5) * 0.4, length)
  const middle = at({ x: (from.x + end.x) / 2, y: (from.y + end.y) / 2 }, angle + Math.PI / 2, (rnd() - 0.5) * length * 0.5)
  out[depth === 2 ? 'trunks' : 'twigs'].push(`M${fixed(from)} Q${fixed(middle)} ${fixed(end)}`)
  if (depth === 0) {
    out.tips.push(end)
    return
  }
  grow(end, angle - 0.3 - rnd() * 0.5, length * 0.68, depth - 1, rnd, out)
  grow(end, angle + 0.3 + rnd() * 0.5, length * 0.68, depth - 1, rnd, out)
}

const curveLength = (a: Point, b: Point, c: Point, d: Point) => {
  const steps = 24
  let length = 0
  let last = a
  for (let i = 1; i <= steps; i++) {
    const t = i / steps
    const u = 1 - t
    const point = {
      x: u * u * u * a.x + 3 * u * u * t * b.x + 3 * u * t * t * c.x + t * t * t * d.x,
      y: u * u * u * a.y + 3 * u * u * t * b.y + 3 * u * t * t * c.y + t * t * t * d.y,
    }
    length += Math.hypot(point.x - last.x, point.y - last.y)
    last = point
  }
  return length
}

const angleBetween = (a: Point, b: Point) => Math.atan2(b.y - a.y, b.x - a.x)

const build = (index: number): Neuron => {
  const soma = somas[index]
  const next = somas[index + 1]
  const rnd = random(index + 7)
  const axonAngle = next ? angleBetween(soma, next) : null
  const out = { trunks: [] as string[], twigs: [] as string[], tips: [] as Point[] }
  const count = 6
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 + rnd() * 0.5
    const away = axonAngle === null ? Math.PI : Math.abs(Math.atan2(Math.sin(angle - axonAngle), Math.cos(angle - axonAngle)))
    if (away < 0.6) continue
    grow(at(soma, angle, SOMA_RADIUS - 1), angle, 30 + rnd() * 16, 2, rnd, out)
  }
  let axon: string | null = null
  let axonLength = 0
  let terminal: Point | null = null
  if (next && axonAngle !== null) {
    const start = at(soma, axonAngle, SOMA_RADIUS)
    const distance = Math.hypot(next.x - soma.x, next.y - soma.y)
    terminal = at(next, axonAngle + Math.PI, TERMINAL_GAP)
    const bend = (rnd() - 0.5) * distance * 0.35
    const first = at(at(start, axonAngle, distance * 0.3), axonAngle + Math.PI / 2, bend)
    const second = at(at(start, axonAngle, distance * 0.7), axonAngle + Math.PI / 2, -bend)
    axon = `M${fixed(start)} C${fixed(first)} ${fixed(second)} ${fixed(terminal)}`
    axonLength = curveLength(start, first, second, terminal)
  }
  return { soma, trunks: out.trunks.join(' '), twigs: out.twigs.join(' '), tips: out.tips, axon, axonLength, terminal }
}

export const neurons: Neuron[] = somas.map((_, index) => build(index))

export const cascades: number[][] = [
  [0, 1, 2, 3, 4, 5],
  [3, 4, 5],
]
