import './charts.css'

const WIDTH = 100
const HEIGHT = 32

export function Sparkline({ values }: { values: number[] }) {
  const low = Math.min(...values)
  const range = Math.max(...values) - low || 1
  const points = values.map((value, index) => `${(index / (values.length - 1)) * WIDTH},${HEIGHT - ((value - low) / range) * (HEIGHT - 4) - 2}`)
  return (
    <svg className="sami-spark" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none" role="img" aria-label="Trend">
      <polygon className="sami-spark-area" points={`0,${HEIGHT} ${points.join(' ')} ${WIDTH},${HEIGHT}`} />
      <polyline className="sami-spark-line" points={points.join(' ')} />
    </svg>
  )
}
