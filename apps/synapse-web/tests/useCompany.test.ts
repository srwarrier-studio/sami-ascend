import { act, renderHook } from '@testing-library/react'
import { useCompany } from '../src/session/useCompany'
import type { User } from '../src/session/sessionClient'

const userWith = (companies: string[]): User => ({ userid: 'u1', name: 'N', email: '', roles: [], companies })

beforeEach(() => localStorage.clear())

describe('choosing a company', () => {
  it('picks the only company automatically', () => {
    const { result } = renderHook(() => useCompany(userWith(['organica'])))
    expect(result.current.company).toBe('organica')
  })

  it('has none chosen with several companies', () => {
    const { result } = renderHook(() => useCompany(userWith(['sabinsa', 'organica'])))
    expect(result.current.company).toBeNull()
  })

  it('remembers the choice per user across reloads', () => {
    const user = userWith(['sabinsa', 'organica'])
    const first = renderHook(() => useCompany(user))
    act(() => first.result.current.setCompany('organica'))
    expect(first.result.current.company).toBe('organica')
    expect(localStorage.getItem('synapse.company.u1')).toBe('organica')
    expect(renderHook(() => useCompany(user)).result.current.company).toBe('organica')
  })

  it('ignores a stored company the user no longer has', () => {
    localStorage.setItem('synapse.company.u1', 'neutraceuticals')
    const { result } = renderHook(() => useCompany(userWith(['sabinsa', 'organica'])))
    expect(result.current.company).toBeNull()
  })

  it('refuses a company the user does not have', () => {
    const { result } = renderHook(() => useCompany(userWith(['sabinsa', 'organica'])))
    act(() => result.current.setCompany('neutraceuticals'))
    expect(result.current.company).toBeNull()
  })

  it('has none when signed out', () => {
    expect(renderHook(() => useCompany(null)).result.current.company).toBeNull()
  })
})
