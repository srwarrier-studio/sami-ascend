import { useEffect, useState } from 'react'
import { Select } from '@sami/ui'

export type RemoteOption = { value: string; label: string }

export const SEARCH_DELAY_MS = 250

type Props<T extends RemoteOption> = {
  label: string
  search: (query: string) => Promise<T[]>
  selected: T | null
  onSelect: (option: T | null) => void
  error?: string
  disabled?: boolean
  placeholder?: string
  resetKey?: string
}

export function RemoteSelect<T extends RemoteOption>({ label, search, selected, onSelect, error, disabled, placeholder, resetKey }: Props<T>) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState<T[]>([])
  const [failed, setFailed] = useState(false)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (disabled) return
    let current = true
    const timer = setTimeout(() => {
      search(query).then(
        (found) => {
          if (!current) return
          setOptions(found)
          setFailed(false)
          setLoaded(true)
        },
        () => current && setFailed(true),
      )
    }, SEARCH_DELAY_MS)
    return () => {
      current = false
      clearTimeout(timer)
    }
  }, [search, query, disabled, resetKey])

  const known = selected && !options.some((option) => option.value === selected.value) ? [selected, ...options] : options

  return (
    <Select
      label={label}
      placeholder={placeholder}
      searchable
      clearable
      disabled={disabled}
      data={known}
      value={selected?.value ?? null}
      searchValue={query}
      onSearchChange={setQuery}
      filter={({ options: all }) => all}
      nothingFoundMessage={failed ? 'Could not load the list. Try typing again.' : loaded ? 'No matches' : 'Loading...'}
      error={error}
      comboboxProps={{ withinPortal: false }}
      onChange={(value) => onSelect(known.find((option) => option.value === value) ?? null)}
    />
  )
}
