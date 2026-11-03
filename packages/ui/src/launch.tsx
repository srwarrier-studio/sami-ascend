import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Button, Card, Divider, Group, PasswordInput, Stack, Text, TextInput } from '@mantine/core'
import { SparkleIcon, WarningCircleIcon } from '@phosphor-icons/react'
import classes from './launch.module.css'

export function SplashScreen({ name, tagline, mark }: { name: string; tagline: string; mark?: ReactNode }) {
  return (
    <div className={classes.splash}>
      {mark ?? (
        <span className={classes.mark}>
          <SparkleIcon size={36} weight="fill" />
        </span>
      )}
      <h1 className={classes.name}>{name}</h1>
      <p className={classes.tagline}>{tagline}</p>
      <div className={classes.track} aria-hidden="true">
        <i className={classes.sweep} />
      </div>
    </div>
  )
}

type SignInCardProps = {
  title: string
  error?: string
  busy?: boolean
  onSubmit: (email: string, password: string) => void
  footer?: ReactNode
}

export function SignInCard({ title, error, busy, onSubmit, footer }: SignInCardProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(email, password)
  }
  return (
    <Card className={classes.signin} component="form" onSubmit={submit} shadow="sm">
      <Stack>
        <Group gap="xs">
          <span className={classes.mark} aria-hidden="true">
            <SparkleIcon size={18} weight="fill" />
          </span>
          <Text fw={600} size="lg">
            {title}
          </Text>
        </Group>
        {error && (
          <div className={classes.problem} role="alert">
            <WarningCircleIcon size={18} weight="fill" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
        <TextInput label="Work email" type="email" value={email} onChange={(event) => setEmail(event.currentTarget.value)} required />
        <PasswordInput label="Password" value={password} onChange={(event) => setPassword(event.currentTarget.value)} required />
        <Button type="submit" loading={busy}>
          Sign in
        </Button>
        {footer && (
          <>
            <Divider label="or" labelPosition="center" />
            {footer}
          </>
        )}
      </Stack>
    </Card>
  )
}
