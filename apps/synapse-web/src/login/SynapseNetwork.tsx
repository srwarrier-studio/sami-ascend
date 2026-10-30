import { useEffect, useRef } from 'react'
import { drawNetwork, makeShapes } from './drawNetwork'
import classes from './SynapseNetwork.module.css'

const FRAME = 1000 / 30
const MAX_PIXEL_RATIO = 1.5

export function SynapseNetwork({ animated }: { animated: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const element = canvas.current
    const ctx = element?.getContext('2d')
    if (!element || !ctx) return
    const shapes = makeShapes()
    const started = performance.now()
    let width = 0
    let height = 0
    let frame = 0
    let last = 0

    const draw = (now: number) => drawNetwork(ctx, shapes, width, height, (now - started) / 1000, animated)

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

  return <canvas ref={canvas} className={classes.network} aria-hidden="true" data-animated={animated} />
}
