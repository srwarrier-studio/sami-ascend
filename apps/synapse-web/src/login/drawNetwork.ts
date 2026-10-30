import { neurons, SOMA_RADIUS } from './network'
import type { Point } from './network'
import { drift, flashLevel, hopsFrom, pulseProgress, TRAVEL } from './timeline'

const WIDTH = 800
const HEIGHT = 600
const PULSE_SHARE = 0.07

type Shapes = { twigs: Path2D; trunks: Path2D; axon: Path2D | null }

export const makeShapes = (): Shapes[] =>
  neurons.map((neuron) => ({ twigs: new Path2D(neuron.twigs), trunks: new Path2D(neuron.trunks), axon: neuron.axon ? new Path2D(neuron.axon) : null }))

const dot = (ctx: CanvasRenderingContext2D, point: Point, radius: number, fill: string) => {
  ctx.beginPath()
  ctx.arc(point.x, point.y, radius, 0, Math.PI * 2)
  ctx.fillStyle = fill
  ctx.fill()
}

const stroke = (ctx: CanvasRenderingContext2D, path: Path2D, color: string, width: number) => {
  ctx.strokeStyle = color
  ctx.lineWidth = width
  ctx.stroke(path)
}

const flash = (ctx: CanvasRenderingContext2D, point: Point, radius: number, peak: number, level: number) => {
  if (level <= 0) return
  ctx.globalAlpha = level
  dot(ctx, point, radius + (peak - radius) * level, '#f4faff')
  ctx.globalAlpha = 1
}

export const drawNetwork = (ctx: CanvasRenderingContext2D, shapes: Shapes[], width: number, height: number, time: number, animated: boolean) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, width, height)
  const scale = Math.max(width / WIDTH, height / HEIGHT)
  ctx.setTransform(scale, 0, 0, scale, (width - WIDTH * scale) / 2, (height - HEIGHT * scale) / 2)
  ctx.lineCap = 'round'
  neurons.forEach((neuron, index) => {
    const move = animated ? drift(index, time) : { x: 0, y: 0 }
    ctx.save()
    ctx.translate(move.x, move.y)
    stroke(ctx, shapes[index].twigs, 'rgb(91 141 239 / 16%)', 0.6)
    stroke(ctx, shapes[index].trunks, 'rgb(91 141 239 / 24%)', 1)
    const axon = shapes[index].axon
    if (axon) stroke(ctx, axon, 'rgb(91 141 239 / 28%)', 0.9)
    neuron.tips.forEach((tip) => dot(ctx, tip, 1.3, 'rgb(143 180 255 / 30%)'))
    if (neuron.terminal) dot(ctx, neuron.terminal, 3, 'rgb(91 141 239 / 35%)')
    dot(ctx, neuron.soma, SOMA_RADIUS, '#12286a')
    ctx.beginPath()
    ctx.arc(neuron.soma.x, neuron.soma.y, SOMA_RADIUS, 0, Math.PI * 2)
    ctx.strokeStyle = 'rgb(111 156 255 / 45%)'
    ctx.lineWidth = 1
    ctx.stroke()
    dot(ctx, neuron.soma, 3, 'rgb(143 180 255 / 40%)')
    if (animated && axon && neuron.terminal) {
      hopsFrom(index).forEach((begin) => {
        flash(ctx, neuron.soma, SOMA_RADIUS, SOMA_RADIUS + 6, flashLevel(time, begin))
        flash(ctx, neuron.terminal!, 3, 9, flashLevel(time, begin + TRAVEL))
        const progress = pulseProgress(time, begin)
        if (progress === null) return
        const dash = neuron.axonLength * PULSE_SHARE
        ctx.setLineDash([dash, neuron.axonLength * 2])
        ctx.lineDashOffset = -(progress * (neuron.axonLength + dash) - dash)
        stroke(ctx, axon, 'rgb(143 180 255 / 35%)', 6)
        stroke(ctx, axon, '#e8f3ff', 1.8)
        ctx.setLineDash([])
      })
    }
    ctx.restore()
  })
}
