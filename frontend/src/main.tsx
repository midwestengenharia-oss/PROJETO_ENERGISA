import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AppRouter } from './AppRouter'
import { ToastProvider } from './components/Toast'
import { AuthProvider } from './contexts/AuthContext'
import { PerfilProvider } from './contexts/PerfilContext'
import { ThemeProvider } from './contexts/ThemeContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <PerfilProvider>
            <AppRouter />
          </PerfilProvider>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  </StrictMode>,
)
