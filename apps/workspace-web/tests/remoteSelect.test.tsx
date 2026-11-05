import { useState } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UiProvider, workspacePalette } from '@sami/ui'
import { RemoteSelect } from '../src/components/RemoteSelect'
import type { RemoteOption } from '../src/components/RemoteSelect'

const options: RemoteOption[] = [
  { value: 'M1', label: 'M1 Bolt' },
  { value: 'M2', label: 'M2 Nut' },
]

type Harness = { search: (query: string) => Promise<RemoteOption[]>; disabled?: boolean; error?: string; resetKey?: string }

function Harness({ search, disabled, error, resetKey }: Harness) {
  const [selected, setSelected] = useState<RemoteOption | null>(null)
  return (
    <UiProvider palette={workspacePalette}>
      <RemoteSelect label="Material" search={search} selected={selected} onSelect={setSelected} disabled={disabled} error={error} resetKey={resetKey} />
      <output>{selected ? selected.value : 'none'}</output>
    </UiProvider>
  )
}

const box = () => screen.getAllByLabelText('Material')[0]

describe('RemoteSelect', () => {
  it('lists the first page when opened and shows each hit', async () => {
    const search = vi.fn().mockResolvedValue(options)
    render(<Harness search={search} />)
    await userEvent.click(box())
    expect(await screen.findByText('M1 Bolt')).toBeInTheDocument()
    expect(screen.getByText('M2 Nut')).toBeInTheDocument()
    expect(search).toHaveBeenCalledWith('')
  })

  it('asks once after the user stops typing, with what was typed', async () => {
    const search = vi.fn().mockResolvedValue(options)
    render(<Harness search={search} />)
    await userEvent.click(box())
    await screen.findByText('M1 Bolt')
    search.mockClear()
    await userEvent.type(box(), 'bol')
    await waitFor(() => expect(search).toHaveBeenCalledTimes(1))
    expect(search).toHaveBeenCalledWith('bol')
  })

  it('does not filter the answer itself: the server decides what matches', async () => {
    const search = vi.fn().mockResolvedValue(options)
    render(<Harness search={search} />)
    await userEvent.type(box(), 'zzz')
    expect(await screen.findByText('M1 Bolt')).toBeInTheDocument()
  })

  it('keeps the chosen option when the list changes', async () => {
    const search = vi.fn().mockResolvedValueOnce(options).mockResolvedValue([{ value: 'M9', label: 'M9 Washer' }])
    render(<Harness search={search} />)
    await userEvent.click(box())
    await userEvent.click(await screen.findByText('M2 Nut'))
    expect(screen.getByRole('status')).toHaveTextContent('M2')
    await userEvent.clear(box())
    await userEvent.type(box(), 'w')
    await screen.findByText('M9 Washer')
    expect(screen.getByRole('status')).toHaveTextContent('M2')
  })

  it('says no matches when the server finds none', async () => {
    render(<Harness search={vi.fn().mockResolvedValue([])} />)
    await userEvent.click(box())
    expect(await screen.findByText('No matches')).toBeInTheDocument()
  })

  it('says so when the list cannot be loaded and tries again on the next typing', async () => {
    const search = vi.fn().mockRejectedValueOnce(new Error('down')).mockResolvedValue(options)
    render(<Harness search={search} />)
    await userEvent.click(box())
    expect(await screen.findByText('Could not load the list. Try typing again.')).toBeInTheDocument()
    await userEvent.type(box(), 'b')
    expect(await screen.findByText('M1 Bolt')).toBeInTheDocument()
  })

  it('does not ask the server while disabled', async () => {
    const search = vi.fn().mockResolvedValue(options)
    render(<Harness search={search} disabled />)
    await new Promise((resolve) => setTimeout(resolve, 400))
    expect(box()).toBeDisabled()
    expect(search).not.toHaveBeenCalled()
  })

  it('shows an error under the field', () => {
    render(<Harness search={vi.fn().mockResolvedValue([])} error="No such material" />)
    expect(screen.getByText('No such material')).toBeInTheDocument()
  })

  it('asks again when the reset key changes', async () => {
    const search = vi.fn().mockResolvedValue(options)
    const { rerender } = render(<Harness search={search} resetKey="1000" />)
    await waitFor(() => expect(search).toHaveBeenCalledTimes(1))
    rerender(<Harness search={search} resetKey="2000" />)
    await waitFor(() => expect(search).toHaveBeenCalledTimes(2))
  })
})
