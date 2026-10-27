import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from './App.tsx'
import { authClient } from './api/auth'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UiProvider palette={workspacePalette}>
      <App client={authClient} />
    </UiProvider>
  </StrictMode>,
)
