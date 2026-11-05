import { useState } from 'react'
import { useRouteContext, useSearch } from '@tanstack/react-router'
import { Button, LoginLayout } from '@sami/ui'
import { entraLoginUrl } from '../api/auth'
import { WorkspaceLogo } from '../brand/WorkspaceLogo'
import { APP_NAME, TAGLINE } from '../config'
import { Honeycomb } from '../login/Honeycomb'

const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

const ENTRA_FAILED = 'Microsoft sign-in failed. Ask an admin to check your account.'

function MicrosoftMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 21 21" aria-hidden="true" focusable="false">
      <rect x="1" y="1" width="9" height="9" fill="#f25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
      <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
      <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
    </svg>
  )
}

export function LoginPage() {
  const { login } = useRouteContext({ from: '/login' })
  const { error } = useSearch({ from: '/login' })
  const [problem, setProblem] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (email: string, password: string) => {
    setBusy(true)
    setProblem(null)
    try {
      if (!(await login(email, password))) setProblem('Incorrect email or password')
    } catch {
      setProblem('Cannot reach the sign-in service. Try again in a moment.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <LoginLayout
      background={<Honeycomb animated={!prefersReducedMotion()} />}
      logo={<WorkspaceLogo size={72} />}
      name={APP_NAME}
      tagline={TAGLINE}
      title={`Sign in to ${APP_NAME}`}
      error={problem ?? (error === 'entra' ? ENTRA_FAILED : undefined)}
      busy={busy}
      onSubmit={submit}
      footer={
        <Button component="a" href={entraLoginUrl} variant="default" data-login-alt leftSection={<MicrosoftMark />}>
          Sign in with Microsoft
        </Button>
      }
    />
  )
}
