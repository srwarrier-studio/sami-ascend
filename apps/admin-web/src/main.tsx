import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { UiProvider, presets } from '@sami/ui'
import App from './App.tsx'
import { authClient } from './api/auth'
import { adminClient } from './api/adminClient'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UiProvider palette={presets.graphite}>
      <App client={authClient} admin={adminClient} />
    </UiProvider>
  </StrictMode>,
)
