import { cellsFor, radiusFor, twinkleLevel } from './honeycomb'
import type { Cell } from './honeycomb'

export type Colors = { line: string; fill: string }

const SIDES = 6
const LIT_FROM = 0.12

const outline = (ctx: CanvasRenderingContext2D, cell: Cell, radius: number) => {
  for (let side = 0; side < SIDES; side++) {
    const angle = Math.PI / 6 + (side * Math.PI) / 3
    const x = cell.x + Math.cos(angle) * radius
    const y = cell.y + Math.sin(angle) * radius
    if (side === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
    if (side === SIDES - 1) ctx.closePath()
  }
}

export const drawHoneycomb = (ctx: CanvasRenderingContext2D, colors: Colors, width: number, height: number, time: number) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, width, height)
  const radius = radiusFor(width) - 1.5
  const cells = cellsFor(width, height)
  ctx.lineWidth = 1
  ctx.globalAlpha = 0.07
  ctx.strokeStyle = colors.line
  ctx.beginPath()
  cells.forEach((cell) => outline(ctx, cell, radius))
  ctx.stroke()
  cells.forEach((cell, index) => {
    const level = twinkleLevel(index, time)
    if (level < LIT_FROM) return
    ctx.beginPath()
    outline(ctx, cell, radius)
    ctx.globalAlpha = level * 0.32
    ctx.fillStyle = colors.fill
    ctx.fill()
    ctx.globalAlpha = level * 0.325
    ctx.strokeStyle = colors.line
    ctx.stroke()
  })
  ctx.globalAlpha = 1
}
