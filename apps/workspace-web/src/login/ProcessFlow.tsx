import { useEffect, useRef } from 'react'
import { drawFlow } from './drawFlow'
import type { Colors } from './drawFlow'
import classes from './ProcessFlow.module.css'

const FRAME = 1000 / 30
const MAX_PIXEL_RATIO = 1.5

const readColors = (element: HTMLElement): Colors => {
  const style = getComputedStyle(element)
  const shade = (n: number) => style.getPropertyValue(`--mantine-color-brand-${n}`).trim() || 'white'
  return { ground: shade(9), line: shade(3), glow: shade(4), card: shade(1), ink: shade(2) }
}

export function ProcessFlow({ animated }: { animated: boolean }) {
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

    const draw = (now: number) => drawFlow(ctx, colors, width, height, (now - started) / 1000, animated)

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
      draw(now)
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

  return <canvas ref={canvas} className={classes.flow} aria-hidden="true" data-animated={animated} />
}
