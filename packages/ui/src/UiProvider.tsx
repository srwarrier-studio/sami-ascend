import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import './motion.css'
import './premium.css'
import { MantineProvider, createTheme } from '@mantine/core'
import type { CSSVariablesResolver } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { useLayoutEffect } from 'react'
import type { ReactNode } from 'react'
import { premiumSurfaces } from './palettes'
import type { Palette, Surfaces } from './palettes'
import { createSharedTheme } from './theme'
import type { RadiusMode } from './theme'

export type MotionMode = 'full' | 'minimal'
export type Look = 'standard' | 'premium'

type UiProviderProps = {
  palette: Palette
  radius?: RadiusMode
  motion?: MotionMode
  look?: Look
  children: ReactNode
}

const variablesOf = (surfaces: Surfaces) => ({
  '--sami-canvas': surfaces.canvas,
  '--sami-surface': surfaces.surface,
  '--sami-border': surfaces.border,
  '--sami-shadow': surfaces.shadow,
})

const premiumResolver: CSSVariablesResolver = () => ({
  variables: {},
  light: variablesOf(premiumSurfaces.light),
  dark: variablesOf(premiumSurfaces.dark),
})

export function UiProvider({ palette, radius = 'soft', motion = 'full', look = 'standard', children }: UiProviderProps) {
  useLayoutEffect(() => {
    document.documentElement.dataset.motion = motion
    return () => document.documentElement.removeAttribute('data-motion')
  }, [motion])

  useLayoutEffect(() => {
    if (look === 'standard') return
    document.documentElement.dataset.look = look
    return () => document.documentElement.removeAttribute('data-look')
  }, [look])

  const theme = createTheme({
    ...createSharedTheme(radius),
    colors: palette.colors,
    primaryColor: palette.primaryColor,
    primaryShade: palette.primaryShade as 6,
  })
  return <MantineProvider theme={theme} cssVariablesResolver={look === 'premium' ? premiumResolver : undefined}>
      <Notifications position="top-center" />
      {children}
    </MantineProvider>
}
