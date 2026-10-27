import '@mantine/core/styles.css'
import { MantineProvider, createTheme } from '@mantine/core'
import type { ReactNode } from 'react'
import type { Palette } from './palettes'
import { sharedTheme } from './theme'

type UiProviderProps = {
  palette: Palette
  children: ReactNode
}

export function UiProvider({ palette, children }: UiProviderProps) {
  const theme = createTheme({
    ...sharedTheme,
    colors: palette.colors,
    primaryColor: palette.primaryColor,
    primaryShade: palette.primaryShade as 6,
  })
  return <MantineProvider theme={theme}>{children}</MantineProvider>
}
