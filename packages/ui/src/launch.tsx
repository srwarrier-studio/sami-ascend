import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button, Card, Group, PasswordInput, Stack, Text, TextInput } from '@mantine/core'
import { SparkleIcon } from '@phosphor-icons/react'
import { Alert } from './Alert'
import classes from './launch.module.css'

export function SplashScreen({ name, tagline }: { name: string; tagline: string }) {
  return (
    <div className={classes.splash}>
      <span className={classes.mark}>
        <SparkleIcon size={36} weight="fill" />
      </span>
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
}

export function SignInCard({ title, error, busy, onSubmit }: SignInCardProps) {
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
        {error && <Alert color="red">{error}</Alert>}
        <TextInput label="Work email" type="email" value={email} onChange={(event) => setEmail(event.currentTarget.value)} required />
        <PasswordInput label="Password" value={password} onChange={(event) => setPassword(event.currentTarget.value)} required />
        <Button type="submit" loading={busy}>
          Sign in
        </Button>
      </Stack>
    </Card>
  )
}
