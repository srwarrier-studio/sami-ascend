import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import { MantineProvider, createTheme } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import type { ReactNode } from 'react'
import type { Palette } from './palettes'
import { createSharedTheme } from './theme'
import type { RadiusMode } from './theme'

type UiProviderProps = {
  palette: Palette
  radius?: RadiusMode
  children: ReactNode
}

export function UiProvider({ palette, radius = 'soft', children }: UiProviderProps) {
  const theme = createTheme({
    ...createSharedTheme(radius),
    colors: palette.colors,
    primaryColor: palette.primaryColor,
    primaryShade: palette.primaryShade as 6,
  })
  return <MantineProvider theme={theme}>
      <Notifications />
      {children}
    </MantineProvider>
}
