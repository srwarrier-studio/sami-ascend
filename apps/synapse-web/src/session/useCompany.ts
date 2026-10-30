import { useCallback, useState } from 'react'
import type { User } from './sessionClient'

const key = (userid: string) => `synapse.company.${userid}`

const stored = (user: User) => {
  try {
    return localStorage.getItem(key(user.userid))
  } catch {
    return null
  }
}

export function useCompany(user: User | null) {
  const [, rerender] = useState(0)

  const setCompany = useCallback(
    (id: string) => {
      if (!user?.companies.includes(id)) return
      try {
        localStorage.setItem(key(user.userid), id)
      } catch {
        return
      }
      rerender((n) => n + 1)
    },
    [user],
  )

  if (!user) return { company: null, setCompany }
  if (user.companies.length === 1) return { company: user.companies[0], setCompany }
  const chosen = stored(user)
  return { company: chosen && user.companies.includes(chosen) ? chosen : null, setCompany }
}
