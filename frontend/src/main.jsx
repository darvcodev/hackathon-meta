import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import Inicio from './pages/Inicio.jsx'
import Finca from './pages/Finca.jsx'
import Roya from './pages/Roya.jsx'
import Maduracion from './pages/Maduracion.jsx'
import Camara from './pages/Camara.jsx'
import Asistente from './pages/Asistente.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/finca" element={<Finca />} />
        <Route path="/roya/:id?" element={<Roya />} />
        <Route path="/maduracion/:id?" element={<Maduracion />} />
        <Route path="/camara" element={<Camara />} />
        <Route path="/asistente" element={<Asistente />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
