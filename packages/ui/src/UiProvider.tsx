import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import './motion.css'
import { MantineProvider, createTheme } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { useLayoutEffect } from 'react'
import type { ReactNode } from 'react'
import type { Palette } from './palettes'
import { createSharedTheme } from './theme'
import type { RadiusMode } from './theme'

export type MotionMode = 'full' | 'minimal'

type UiProviderProps = {
  palette: Palette
  radius?: RadiusMode
  motion?: MotionMode
  children: ReactNode
}

export function UiProvider({ palette, radius = 'soft', motion = 'full', children }: UiProviderProps) {
  useLayoutEffect(() => {
    document.documentElement.dataset.motion = motion
    return () => document.documentElement.removeAttribute('data-motion')
  }, [motion])

  const theme = createTheme({
    ...createSharedTheme(radius),
    colors: palette.colors,
    primaryColor: palette.primaryColor,
    primaryShade: palette.primaryShade as 6,
  })
  return <MantineProvider theme={theme}>
      <Notifications position="top-center" />
      {children}
    </MantineProvider>
}
