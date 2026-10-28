import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import classes from './Notification.module.css'
import { Alert, Button, Card, Input, Menu, Modal, Notification, createTheme, rem } from '@mantine/core'

export const fontFamily = '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

const controlHeights: Record<string, string> = {
  xs: rem(24),
  sm: rem(32),
  md: rem(40),
  lg: rem(48),
  xl: rem(56),
}

const controlHeight = (size: unknown) => controlHeights[typeof size === 'string' ? size : 'sm']

const buttonPaddings: Record<string, string> = { xs: rem(12), sm: rem(16), md: rem(20) }

export type RadiusMode = 'soft' | 'sharp'

const radii = {
  soft: { xs: rem(4), sm: rem(6), md: rem(12), lg: rem(16), xl: rem(999) },
  sharp: { xs: rem(4), sm: rem(4), md: rem(4), lg: rem(4), xl: rem(4) },
}

export const createSharedTheme = (radius: RadiusMode) => createTheme({
  defaultRadius: 'sm',
  fontFamily,
  fontSmoothing: true,
  cursorType: 'pointer',
  fontSizes: { xs: rem(12), sm: rem(14), md: rem(14), lg: rem(16), xl: rem(20) },
  lineHeights: { xs: '1.33', sm: '1.43', md: '1.43', lg: '1.5', xl: '1.4' },
  spacing: { xs: rem(4), sm: rem(8), md: rem(16), lg: rem(24), xl: rem(32) },
  radius: radii[radius],
  headings: {
    fontFamily,
    fontWeight: '600',
    sizes: {
      h1: { fontSize: rem(28), lineHeight: '1.25' },
      h2: { fontSize: rem(24), lineHeight: '1.3' },
      h3: { fontSize: rem(20), lineHeight: '1.4' },
      h4: { fontSize: rem(16), lineHeight: '1.5' },
      h5: { fontSize: rem(14), lineHeight: '1.43' },
      h6: { fontSize: rem(12), lineHeight: '1.33' },
    },
  },
  components: {
    Button: Button.extend({
      defaultProps: { size: 'sm', fw: 500, radius: 'xl' },
      vars: (_, props) => ({
        root: {
          '--button-height': controlHeight(props.size),
          '--button-padding-x': buttonPaddings[typeof props.size === 'string' ? props.size : 'sm'],
        },
      }),
    }),
    Input: Input.extend({
      vars: (_, props) => ({ wrapper: { '--input-height': controlHeight(props.size) } }),
    }),
    TextInput: { defaultProps: { size: 'sm' } },
    PasswordInput: { defaultProps: { size: 'sm' } },
    Card: Card.extend({ defaultProps: { withBorder: true, padding: 'md', radius: 'lg' } }),
    Modal: Modal.extend({ defaultProps: { radius: 'lg' } }),
    Menu: Menu.extend({ defaultProps: { radius: 'md' } }),
    Notification: Notification.extend({ classNames: classes, defaultProps: { radius: 'md' } }),
    Alert: Alert.extend({ defaultProps: { variant: 'light', radius: 'md' } }),
  },
})
