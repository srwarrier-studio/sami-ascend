import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { UiProvider, presets } from '@sami/ui'
import App from './App.tsx'
import type { UiSettings } from './router'
import { MockSessionClient } from './session/sessionClient'

const client = new MockSessionClient()

function Root() {
  const [ui, setUi] = useState<UiSettings>({ palette: 'teal', motion: 'full' })
  return (
    <UiProvider palette={presets[ui.palette]} motion={ui.motion}>
      <App client={client} ui={ui} onUiChange={setUi} />
    </UiProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
