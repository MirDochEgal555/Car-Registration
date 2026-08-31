import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles/index.css'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Das Root-Element konnte nicht gefunden werden.')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
