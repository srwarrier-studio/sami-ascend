import { jsPDF } from 'jspdf'
import { toPng } from 'html-to-image'

export type BoardExporter = {
  export: (element: HTMLElement, fileName: string) => Promise<void>
}

const PIXEL_RATIO = 3
const MM_PER_PX = 25.4 / 96

export class PdfBoardExporter implements BoardExporter {
  async export(element: HTMLElement, fileName: string) {
    await document.fonts.ready
    const image = await toPng(element, { pixelRatio: PIXEL_RATIO })
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
