export type Point = { x: number; y: number }

export const nodes: Point[] = [
  [60, 90], [170, 40], [290, 110], [410, 50], [530, 120], [650, 60], [740, 150],
  [110, 210], [230, 250], [350, 190], [470, 260], [590, 210], [700, 290],
  [50, 330], [160, 390], [280, 340], [400, 400], [520, 350], [640, 410], [750, 380],
  [100, 500], [240, 540], [380, 510], [560, 530],
].map(([x, y]) => ({ x, y }))

const REACH = 150

const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y)

export const edges: [number, number][] = nodes.flatMap((a, i) =>
  nodes.flatMap((b, j) => (j > i && distance(a, b) <= REACH ? [[i, j] as [number, number]] : [])),
)

const neighbours = (index: number) =>
  edges.flatMap(([a, b]) => (a === index ? [b] : b === index ? [a] : [])).sort((a, b) => a - b)

const walk = (start: number, length: number) => {
  const chain = [start]
  while (chain.length < length) {
    const next = neighbours(chain[chain.length - 1]).find((candidate) => !chain.includes(candidate))
    if (next === undefined) break
    chain.push(next)
  }
  return chain
}

export const chains = [0, 7, 13, 19, 4, 22].map((start) => walk(start, 6))
