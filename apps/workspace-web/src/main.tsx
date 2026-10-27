import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { UiProvider, workspacePalette } from '@sami/ui'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <UiProvider palette={workspacePalette}>
      <App />
    </UiProvider>
  </StrictMode>,
)
