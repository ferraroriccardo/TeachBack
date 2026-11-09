import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import '@fontsource-variable/bricolage-grotesque'
import '@fontsource/instrument-sans/400.css'
import '@fontsource/instrument-sans/500.css'
import '@fontsource/instrument-sans/600.css'
import './styles/base.css'
import './styles/dashboard.css'
import './styles/loop.css'
import Dashboard from './pages/Dashboard'
import Loop from './pages/Loop'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/course/:courseId" element={<Loop />} />
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
