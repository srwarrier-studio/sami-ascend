import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockBoardExporter } from '../src/export/boardExporter'
import { MockSessionClient } from '../src/session/sessionClient'

const store = () => new MockBoardStore([{ id: 'b1', name: 'Sales / Q4', widgets: [{ id: 'w1', catalogId: 'top-customers' }] }])

const open = (catalogClient = new MockCatalogClient()) => {
  const exporter = new MockBoardExporter()
  render(
    <UiProvider palette={synapsePalette}>
      <App
        client={new MockSessionClient('manager@mock-sami.com')}
        catalogClient={catalogClient}
        boardStore={store()}
        boardExporter={exporter}
        history={createMemoryHistory({ initialEntries: ['/'] })}
      />
    </UiProvider>,
  )
  return exporter
}

describe('Export PDF button', () => {
  it('exports the board frame once with a safe file name and the date', async () => {
    const exporter = open()
    await screen.findByText('Top customers')
    await userEvent.click(screen.getByRole('button', { name: 'Export PDF' }))
    expect(exporter.exported).toHaveLength(1)
    expect(exporter.exported[0].fileName).toBe(`Sales - Q4-${new Date().toLocaleDateString('en-CA')}.pdf`)
    expect(exporter.exported[0].element).toContainElement(screen.getByText('Top customers'))
  })

  it('is hidden in Edit mode', async () => {
    open()
    await userEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    expect(screen.queryByRole('button', { name: 'Export PDF' })).toBeNull()
  })

  it('shows the header and footer only while the export runs', async () => {
    const seen: string[] = []
    const exporter = open()
    exporter.export = async (element) => {
      seen.push(element.textContent ?? '')
    }
    await screen.findByText('Top customers')
    await userEvent.click(screen.getByRole('button', { name: 'Export PDF' }))
    expect(seen[0]).toContain('Mock Manager')
    expect(screen.getByText(/Generated/)).not.toBeVisible()
  })

  it('does not export while a widget is still loading', async () => {
    const mock = new MockCatalogClient()
    const exporter = open({ list: () => mock.list(null), data: () => new Promise(() => undefined) } as unknown as MockCatalogClient)
    await userEvent.click(await screen.findByRole('button', { name: 'Export PDF' }))
    expect(exporter.exported).toHaveLength(0)
    expect(await screen.findByText('Widgets are still loading')).toBeInTheDocument()
  })
})
