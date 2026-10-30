import { render, screen } from '@testing-library/react'
import { UiProvider, synapsePalette } from '@sami/ui'
import { ExportFrame } from '../src/export/ExportFrame'

const generatedAt = new Date('2026-10-30T09:15:00')

const frame = (exporting: boolean) =>
  render(
    <UiProvider palette={synapsePalette}>
      <ExportFrame exporting={exporting} userName="Asha Rao" generatedAt={generatedAt}>
        <p>Board body</p>
      </ExportFrame>
    </UiProvider>,
  )

describe('while exporting', () => {
  it('shows the placeholder logo and company name above the board', () => {
    frame(true)
    expect(screen.getByRole('heading', { name: 'Company name' })).toBeVisible()
    expect(screen.getByText('C')).toBeVisible()
  })

  it('shows when it was generated and by whom below the board', () => {
    frame(true)
    expect(screen.getByText(`Generated ${generatedAt.toLocaleString()} by Asha Rao`)).toBeVisible()
  })
})

describe('when not exporting', () => {
  it('shows only the board', () => {
    frame(false)
    expect(screen.getByText('Board body')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Company name', hidden: true })).not.toBeVisible()
    expect(screen.getByText(/Generated/)).not.toBeVisible()
  })
})
