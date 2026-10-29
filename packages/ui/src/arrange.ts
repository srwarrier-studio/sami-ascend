type Shape = { w: number; h: number }

export const arrange = <T>(items: T[], shape: (item: T) => Shape): T[] => {
  const rest = [...items]
  const result: T[] = []
  while (rest.length) {
    const first = rest.shift() as T
    const { h } = shape(first)
    let free = 12 - shape(first).w
    result.push(first)
    for (let index = 0; index < rest.length && free > 0; ) {
      const candidate = shape(rest[index])
      if (candidate.h === h && candidate.w <= free) {
        free -= candidate.w
        result.push(...rest.splice(index, 1))
      } else {
        index += 1
      }
    }
  }
  return result
}
