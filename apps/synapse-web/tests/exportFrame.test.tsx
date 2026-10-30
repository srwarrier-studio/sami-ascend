import { render, screen } from '@testing-library/react'
import { UiProvider, synapsePalette } from '@sami/ui'
import { ExportFrame } from '../src/export/ExportFrame'

const generatedAt = new Date('2026-10-30T09:15:00')

const frame = (exporting: boolean) =>
  render(
    <UiProvider palette={synapsePalette}>
      <ExportFrame exporting={exporting} userName="Asha Rao" company="organica" generatedAt={generatedAt}>
        <p>Board body</p>
      </ExportFrame>
    </UiProvider>,
  )

describe('while exporting', () => {
  it('covers the page so the header and footer are not seen on screen', () => {
    frame(true)
    expect(screen.getByRole('status')).toHaveTextContent('Preparing PDF')
  })

  it("shows the chosen company's logo and name above the board", () => {
    frame(true)
    expect(screen.getByRole('heading', { name: 'Organica Aromatic' })).toBeVisible()
    expect(screen.getByText('O')).toBeVisible()
  })

  it('shows when it was generated and by whom below the board', () => {
    frame(true)
    expect(screen.getByText(`Generated ${generatedAt.toLocaleString()} by Asha Rao`)).toBeVisible()
  })
})

describe('when not exporting', () => {
  it('has no cover over the page', () => {
    frame(false)
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('shows only the board', () => {
    frame(false)
    expect(screen.getByText('Board body')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Organica Aromatic', hidden: true })).not.toBeVisible()
    expect(screen.getByText(/Generated/)).not.toBeVisible()
  })
})
