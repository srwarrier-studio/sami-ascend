import { toPng } from 'html-to-image'
import { PdfBoardExporter } from '../src/export/boardExporter'

const pdf = vi.hoisted(() => ({ options: undefined as unknown, addImage: vi.fn(), save: vi.fn() }))

vi.mock('html-to-image', () => ({ toPng: vi.fn().mockResolvedValue('data:image/png;base64,AAAA') }))
vi.mock('jspdf', () => ({
  jsPDF: class {
    constructor(options: unknown) {
      pdf.options = options
    }
    addImage = pdf.addImage
    save = pdf.save
  },
}))

const sheet = (width: number, height: number) => {
  const element = document.createElement('div')
  Object.defineProperty(element, 'offsetWidth', { value: width })
  Object.defineProperty(element, 'offsetHeight', { value: height })
  return element
}

beforeEach(() => {
  vi.clearAllMocks()
  Object.defineProperty(document, 'fonts', { value: { ready: Promise.resolve() }, configurable: true })
})

describe('exporting a board to PDF', () => {
  it('pins stylesheet paint onto svg shapes during the capture and puts the styles back after', async () => {
    const style = document.createElement('style')
    style.textContent = '.bar { fill: rgb(255, 0, 0); opacity: 0.12; }'
    document.head.append(style)
    const element = sheet(960, 1200)
    element.innerHTML = '<svg><path class="bar" style="stroke-width: 4"></path></svg>'
    const path = element.querySelector('path')!
    let during: { fill: string; opacity: string } | undefined
    vi.mocked(toPng).mockImplementationOnce(async () => {
      during = { fill: path.style.fill, opacity: path.style.opacity }
      return 'data:image/png;base64,AAAA'
    })
    await new PdfBoardExporter().export(element, 'Bars.pdf')
    expect(during).toEqual({ fill: 'rgb(255, 0, 0)', opacity: '0.12' })
    expect(path.getAttribute('style')).toBe('stroke-width: 4')
    style.remove()
  })

  it('captures at 3x pixel ratio', async () => {
    const element = sheet(960, 1200)
    await new PdfBoardExporter().export(element, 'Sales-2026-10-30.pdf')
    expect(toPng).toHaveBeenCalledWith(element, { pixelRatio: 3 })
  })

  it('makes one page sized to the capture and saves the file name', async () => {
    await new PdfBoardExporter().export(sheet(960, 1200), 'Sales-2026-10-30.pdf')
    const mm = 25.4 / 96
    expect(pdf.options).toEqual({ orientation: 'portrait', unit: 'mm', format: [960 * mm, 1200 * mm] })
    expect(pdf.addImage).toHaveBeenCalledWith('data:image/png;base64,AAAA', 'PNG', 0, 0, 960 * mm, 1200 * mm)
    expect(pdf.save).toHaveBeenCalledWith('Sales-2026-10-30.pdf')
  })

  it('uses landscape for a wide board', async () => {
    await new PdfBoardExporter().export(sheet(1600, 900), 'Wide.pdf')
    expect(pdf.options).toMatchObject({ orientation: 'landscape' })
  })
})
