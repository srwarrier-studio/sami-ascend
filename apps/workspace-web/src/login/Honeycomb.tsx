import { useEffect, useRef } from 'react'
import { drawHoneycomb } from './drawHoneycomb'
import type { Colors } from './drawHoneycomb'
import { FrameMeter } from './frameMeter'
import classes from './Honeycomb.module.css'

const FRAME = 1000 / 24
const MAX_PIXEL_RATIO = 1.5

const readColors = (element: HTMLElement): Colors => {
  const style = getComputedStyle(element)
  const shade = (n: number) => style.getPropertyValue(`--mantine-color-brand-${n}`).trim() || 'white'
  return { line: shade(3), fill: shade(6) }
}

export function Honeycomb({ animated }: { animated: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const element = canvas.current
    const ctx = element?.getContext('2d')
    if (!element || !ctx) return
    const colors = readColors(element)
    const started = performance.now()
    let width = 0
    let height = 0
    let frame = 0
    let last = 0
    const meter = new FrameMeter()

    const draw = (now: number) => drawHoneycomb(ctx, colors, width, height, animated ? (now - started) / 1000 : 0)

    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO)
      width = element.clientWidth * ratio
      height = element.clientHeight * ratio
      element.width = width
      element.height = height
      draw(performance.now())
    }

    const tick = (now: number) => {
      frame = requestAnimationFrame(tick)
      if (now - last < FRAME) return
      last = now
      const before = performance.now()
      draw(now)
      if (meter.tooSlow(performance.now() - before)) {
        cancelAnimationFrame(frame)
        element.dataset.animated = 'false'
      }
    }

    resize()
    const observer = new ResizeObserver(resize)
    observer.observe(element)
    if (animated) frame = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
    }
  }, [animated])

  return <canvas ref={canvas} className={classes.honeycomb} aria-hidden="true" data-animated={animated} />
}
