import './index.css'
import React from 'react'
import { createRoot } from 'react-dom/client'
import { AppRouter } from './AppRouter'

const container = document.getElementById('root')!
createRoot(container).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
)

