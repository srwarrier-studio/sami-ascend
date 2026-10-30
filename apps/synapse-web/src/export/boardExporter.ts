import { jsPDF } from 'jspdf'
import { toPng } from 'html-to-image'

export type BoardExporter = {
  export: (element: HTMLElement, fileName: string) => Promise<void>
}

const PIXEL_RATIO = 3
const MM_PER_PX = 25.4 / 96

const PAINT = ['fill', 'stroke', 'stroke-width', 'opacity', 'fill-opacity', 'stroke-opacity', 'stroke-linejoin', 'stroke-linecap', 'stroke-dasharray', 'vector-effect', 'stop-color', 'stop-opacity']

const pinPaint = (root: HTMLElement) => {
  const saved = [...root.querySelectorAll<SVGElement>('svg *')].map((node) => {
    const before = node.getAttribute('style')
    const computed = getComputedStyle(node)
    for (const property of PAINT) node.style.setProperty(property, computed.getPropertyValue(property))
    return { node, before }
  })
  return () => {
    for (const { node, before } of saved) {
      if (before === null) node.removeAttribute('style')
      else node.setAttribute('style', before)
    }
  }
}

export class PdfBoardExporter implements BoardExporter {
  async export(element: HTMLElement, fileName: string) {
    await document.fonts.ready
    const unpin = pinPaint(element)
    const image = await toPng(element, { pixelRatio: PIXEL_RATIO }).finally(unpin)
    const width = element.offsetWidth * MM_PER_PX
    const height = element.offsetHeight * MM_PER_PX
    const pdf = new jsPDF({ orientation: width > height ? 'landscape' : 'portrait', unit: 'mm', format: [width, height] })
    pdf.addImage(image, 'PNG', 0, 0, width, height)
    pdf.save(fileName)
  }
}

export class MockBoardExporter implements BoardExporter {
  readonly exported: { element: HTMLElement; fileName: string }[] = []

  async export(element: HTMLElement, fileName: string) {
    this.exported.push({ element, fileName })
  }
}
