import { links, pointOn, STATION_SIZE, stations } from './flow'
import type { Point, Station } from './flow'
import { arrivalsAt, departures, glowLevel, travelProgress } from './timeline'

const WIDTH = 800
const HEIGHT = 600
const HALF = STATION_SIZE / 2
const CARD_WIDTH = 15
const CARD_HEIGHT = 19

export type Colors = { ground: string; line: string; glow: string; card: string; ink: string }

const rounded = (ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number) => {
  ctx.beginPath()
  ctx.roundRect(x, y, width, height, radius)
}

const strokes = (ctx: CanvasRenderingContext2D, lines: [number, number, number, number][]) => {
  ctx.beginPath()
  lines.forEach(([x1, y1, x2, y2]) => {
    ctx.moveTo(x1, y1)
    ctx.lineTo(x2, y2)
  })
  ctx.stroke()
}

const page = (ctx: CanvasRenderingContext2D) => {
  rounded(ctx, -8, -11, 16, 22, 2)
  ctx.stroke()
}

const icons: Record<string, (ctx: CanvasRenderingContext2D) => void> = {
  requisition: (ctx) => {
    strokes(ctx, [[-4, -6, 8, -6], [-4, 0, 8, 0], [-4, 6, 8, 6]])
    strokes(ctx, [[-9, -6, -8, -6], [-9, 0, -8, 0], [-9, 6, -8, 6]])
  },
  order: (ctx) => {
    page(ctx)
    strokes(ctx, [[-4, -4, 4, -4], [-4, 1, 4, 1], [-4, 6, 1, 6]])
  },
  receipt: (ctx) => {
    rounded(ctx, -10, -7, 20, 15, 2)
    ctx.stroke()
    strokes(ctx, [[-10, -2, 10, -2], [-3, -2, -3, 3], [3, -2, 3, 3]])
  },
  invoice: (ctx) => {
    page(ctx)
    strokes(ctx, [[-4, -5, 4, -5], [-4, 0, 4, 0]])
    rounded(ctx, -4, 4, 8, 4, 1)
    ctx.stroke()
  },
  payment: (ctx) => {
    ctx.beginPath()
    ctx.arc(0, 0, 10, 0, Math.PI * 2)
    ctx.moveTo(5, 0)
    ctx.arc(0, 0, 5, 0, Math.PI * 2)
    ctx.stroke()
  },
}

const drawStation = (ctx: CanvasRenderingContext2D, station: Station, colors: Colors, level: number) => {
  ctx.save()
  ctx.translate(station.x, station.y)
  if (level > 0) {
    ctx.globalAlpha = level * 0.35
    rounded(ctx, -HALF - 7, -HALF - 7, STATION_SIZE + 14, STATION_SIZE + 14, 18)
    ctx.fillStyle = colors.glow
    ctx.fill()
  }
  ctx.globalAlpha = 0.85
  rounded(ctx, -HALF, -HALF, STATION_SIZE, STATION_SIZE, 12)
  ctx.fillStyle = colors.ground
  ctx.fill()
  ctx.globalAlpha = 0.3 + level * 0.4
  ctx.lineWidth = 1
  ctx.strokeStyle = colors.line
  ctx.stroke()
  ctx.globalAlpha = 0.45 + level * 0.4
  ctx.lineWidth = 1.5
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = colors.ink
  icons[station.id](ctx)
  ctx.restore()
}

const drawCard = (ctx: CanvasRenderingContext2D, at: Point, colors: Colors) => {
  ctx.save()
  ctx.translate(at.x, at.y)
  ctx.globalAlpha = 0.9
  rounded(ctx, -CARD_WIDTH / 2, -CARD_HEIGHT / 2, CARD_WIDTH, CARD_HEIGHT, 3)
  ctx.fillStyle = colors.card
  ctx.fill()
  ctx.globalAlpha = 0.5
  ctx.lineWidth = 1.2
  ctx.strokeStyle = colors.ground
  strokes(ctx, [[-4, -3, 4, -3], [-4, 2, 2, 2]])
  ctx.restore()
}

export const drawFlow = (ctx: CanvasRenderingContext2D, colors: Colors, width: number, height: number, time: number, animated: boolean) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, width, height)
  const scale = Math.max(width / WIDTH, height / HEIGHT)
  ctx.setTransform(scale, 0, 0, scale, (width - WIDTH * scale) / 2, (height - HEIGHT * scale) / 2)
  ctx.lineCap = 'round'
  links.forEach((link) => {
    ctx.beginPath()
    ctx.moveTo(link.from.x, link.from.y)
    ctx.quadraticCurveTo(link.bend.x, link.bend.y, link.to.x, link.to.y)
    ctx.globalAlpha = 0.28
    ctx.lineWidth = 1.2
    ctx.setLineDash([2, 7])
    ctx.strokeStyle = colors.line
    ctx.stroke()
    ctx.setLineDash([])
  })
  ctx.globalAlpha = 1
  stations.forEach((station, index) => {
    const level = animated ? Math.max(0, ...arrivalsAt(index).map((begin) => glowLevel(time, begin))) : 0
    drawStation(ctx, station, colors, level)
  })
  if (!animated) return
  links.forEach((link, index) => {
    departures(index).forEach((begin) => {
      const progress = travelProgress(time, begin)
      if (progress !== null) drawCard(ctx, pointOn(link, progress), colors)
    })
  })
}
