import { APP_NAME, TAGLINE } from '../config'
import { useState } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Button, SignInCard, notifications } from '@sami/ui'
import { SynapseLogo } from '../brand/SynapseLogo'
import { SynapseNetwork } from '../login/SynapseNetwork'
import classes from '../login/Login.module.css'
import { useUiSettings } from '../uiSettings'

const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

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
  const { ui } = useUiSettings()
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
    <div className={classes.page}>
      <SynapseNetwork animated={ui.motion === 'full' && !prefersReducedMotion()} />
      <div className={classes.content}>
        <div className={classes.brand}>
          <span className={classes.mark}>
            <SynapseLogo size={72} />
          </span>
          <h1 className={classes.name}>{APP_NAME}</h1>
          <p className={classes.tagline}>{TAGLINE}</p>
        </div>
        <SignInCard
          title={`Sign in to ${APP_NAME}`}
          error={problem ?? undefined}
          busy={busy}
          footer={
            <Button variant="default" className={classes.microsoft} leftSection={<MicrosoftMark />} onClick={() => notifications.show({ message: 'Microsoft sign-in is coming soon' })}>
              Sign in with Microsoft
            </Button>
          }
          onSubmit={submit}
        />
      </div>
    </div>
  )
}
