import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { UiProvider, synapsePalette } from '../src'
import { PageBar } from '../src/PageBar'
import type { PageBarConfig } from '../src/PageBar'

function Bar() {
  const [config, setConfig] = useState<PageBarConfig>({ palette: 'midnight', scheme: 'light', motion: 'full' })
  return <PageBar tabs={[{ id: 'a', name: 'Alpha' }]} activeId="a" config={config} onSelect={() => undefined} onAdd={() => undefined} onConfigChange={setConfig} />
}

describe('the palette picker', () => {
  it('shows the current palette as selected and follows a change', async () => {
    render(
      <UiProvider palette={synapsePalette}>
        <Bar />
      </UiProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Quick settings' }))
    expect(await screen.findByRole('button', { name: 'Midnight', hidden: true })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByText('Copper'))
    expect(screen.getByRole('button', { name: 'Copper', hidden: true })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Midnight', hidden: true })).toHaveAttribute('aria-pressed', 'false')
  })
})
