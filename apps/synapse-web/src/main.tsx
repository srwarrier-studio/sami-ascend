import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from './App.tsx'
import { MockSessionClient } from './session/sessionClient'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient()} />
    </UiProvider>
  </StrictMode>,
)
