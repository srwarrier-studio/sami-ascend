import { createContext, useContext } from 'react'
import type { UiSettings } from './router'

type UiSettingsValue = { ui: UiSettings; setUi: (ui: UiSettings) => void }

export const UiSettingsContext = createContext<UiSettingsValue>({ ui: { palette: 'midnight', motion: 'full' }, setUi: () => undefined })

export const useUiSettings = () => useContext(UiSettingsContext)
