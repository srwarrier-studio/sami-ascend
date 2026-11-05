const SAMPLES = 30
const SLOW_MS = 8

export class FrameMeter {
  private total = 0
  private count = 0

  tooSlow(drawMs: number) {
    this.total += drawMs
    this.count += 1
    if (this.count < SAMPLES) return false
    const slow = this.total / this.count > SLOW_MS
    this.total = 0
    this.count = 0
    return slow
  }
}
