import type { ComponentProps, ReactNode } from 'react'
import { SignInCard } from './launch'
import classes from './LoginLayout.module.css'

type LoginLayoutProps = ComponentProps<typeof SignInCard> & {
  background: ReactNode
  logo: ReactNode
  name: string
  tagline: string
}

export function LoginLayout({ background, logo, name, tagline, ...card }: LoginLayoutProps) {
  return (
    <div className={classes.page}>
      {background}
      <div className={classes.content}>
        <div className={classes.brand}>
          <span className={classes.mark}>{logo}</span>
          <h1 className={classes.name}>{name}</h1>
          <p className={classes.tagline}>{tagline}</p>
        </div>
        <SignInCard {...card} />
      </div>
    </div>
  )
}
