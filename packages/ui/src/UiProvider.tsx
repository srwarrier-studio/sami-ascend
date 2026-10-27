import '@mantine/core/styles.css'
import { MantineProvider, createTheme } from '@mantine/core'
import type { ReactNode } from 'react'
import type { Palette } from './palettes'

const sharedTheme = createTheme({
  defaultRadius: 'md',
  fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  headings: { fontWeight: '600' },
  components: {
    Button: { defaultProps: { size: 'md' } },
    TextInput: { defaultProps: { size: 'md' } },
    PasswordInput: { defaultProps: { size: 'md' } },
    Card: { defaultProps: { withBorder: true, padding: 'lg' } },
    Alert: { defaultProps: { variant: 'light' } },
  },
})

type UiProviderProps = {
  palette: Palette
  children: ReactNode
}

export function UiProvider({ palette, children }: UiProviderProps) {
  const theme = createTheme({
    ...sharedTheme,
    primaryColor: palette.primaryColor,
    primaryShade: palette.primaryShade as 6,
  })
  return <MantineProvider theme={theme}>{children}</MantineProvider>
}
