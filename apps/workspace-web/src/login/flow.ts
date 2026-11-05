export type Point = { x: number; y: number }
export type Station = { id: string; label: string } & Point
export type Link = { from: Station; to: Station; bend: Point }

export const STATION_SIZE = 46

export const stations: Station[] = [
  { id: 'requisition', label: 'Requisition', x: 110, y: 400 },
  { id: 'order', label: 'Order', x: 270, y: 200 },
  { id: 'receipt', label: 'Receipt', x: 430, y: 430 },
  { id: 'invoice', label: 'Invoice', x: 590, y: 190 },
  { id: 'payment', label: 'Payment', x: 700, y: 420 },
]

const bendOf = (from: Station, to: Station): Point => {
  const middle = { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 }
  const sideways = (to.y - from.y) * 0.25
  return { x: middle.x + sideways, y: middle.y - (to.x - from.x) * 0.2 }
}

export const links: Link[] = stations.slice(0, -1).map((from, index) => {
  const to = stations[index + 1]
  return { from, to, bend: bendOf(from, to) }
})

export const pointOn = (link: Link, t: number): Point => {
  const u = 1 - t
  return {
    x: u * u * link.from.x + 2 * u * t * link.bend.x + t * t * link.to.x,
    y: u * u * link.from.y + 2 * u * t * link.bend.y + t * t * link.to.y,
  }
}
