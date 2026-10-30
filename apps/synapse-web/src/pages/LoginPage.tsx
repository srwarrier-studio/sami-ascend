import { APP_NAME } from '../config'
import { useState } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Button, SignInCard, SparkleIcon, notifications } from '@sami/ui'
import { SynapseNetwork } from '../login/SynapseNetwork'
import classes from '../login/Login.module.css'

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
  const { login, ui } = useRouteContext({ from: '/login' })
  const [rejected, setRejected] = useState(false)

  return (
    <div className={classes.page}>
      <SynapseNetwork animated={ui.motion === 'full' && !prefersReducedMotion()} />
      <div className={classes.content}>
        <div className={classes.brand}>
          <span className={classes.mark} aria-hidden="true">
            <SparkleIcon size={28} weight="fill" />
          </span>
          <h1 className={classes.name}>{APP_NAME}</h1>
          <p className={classes.tagline}>Your sales, on one board</p>
        </div>
        <SignInCard
          title={`Sign in to ${APP_NAME}`}
          error={rejected ? 'Incorrect email or password' : undefined}
          footer={
            <Button variant="default" className={classes.microsoft} leftSection={<MicrosoftMark />} onClick={() => notifications.show({ message: 'Microsoft sign-in is coming soon' })}>
              Sign in with Microsoft
            </Button>
          }
          onSubmit={async (email, password) => setRejected(!(await login(email, password)))}
        />
      </div>
    </div>
  )
}
