import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { analizar } from '../api.js'
import { Error, Icono, InsigniaDemo, LOTES, useModo } from '../components/ui.jsx'

const GUIA = { roya: 'Una sola hoja · muestra el envés', maduracion: 'Un racimo · de cerca y de frente' }

export default function Camara() {
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const modo = useModo()
  const video = useRef(null)
  const flujo = useRef(null)
  const galeria = useRef(null)
  const [tipo, setTipo] = useState(parametros.get('tipo') === 'maduracion' ? 'maduracion' : 'roya')
  const [lote, setLote] = useState(Number(parametros.get('lote')) || 1)
  const [enVivo, setEnVivo] = useState(false)
  const [analizando, setAnalizando] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelado = false
    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
      .then((s) => {
        if (cancelado) return s.getTracks().forEach((p) => p.stop())
        flujo.current = s
        video.current.srcObject = s
        setEnVivo(true)
      })
      .catch(() => setEnVivo(false))
    return () => {
      cancelado = true
      flujo.current?.getTracks().forEach((p) => p.stop())
    }
  }, [])

  async function enviar(archivo) {
    setError(null)
    setAnalizando(true)
    try {
      const resultado = await analizar(tipo, archivo, lote)
      navegar(`/${tipo}/${resultado.id}`)
    } catch (e) {
      setError(e.message)
      setAnalizando(false)
    }
  }

  function disparar() {
    // Sin cámara en vivo (por ejemplo sin HTTPS), el celular abre su propia cámara.
    if (!enVivo) return galeria.current.click()
    const v = video.current
    const lienzo = document.createElement('canvas')
    lienzo.width = v.videoWidth
    lienzo.height = v.videoHeight
    lienzo.getContext('2d').drawImage(v, 0, 0)
    lienzo.toBlob((b) => enviar(new File([b], 'captura.jpg', { type: 'image/jpeg' })), 'image/jpeg', 0.92)
  }

  return (
    <div className="relative flex h-dvh justify-center overflow-hidden bg-[#0a1a11] text-white">
      <div className="relative h-full w-full max-w-[480px] overflow-hidden">
        <img src="/img/camara.jpg" alt="" aria-hidden="true" className={`absolute inset-0 size-full object-cover ${enVivo ? 'invisible' : ''}`} />
        <video ref={video} autoPlay playsInline muted className={`absolute inset-0 size-full object-cover ${enVivo ? '' : 'invisible'}`} />

        <div className="absolute inset-x-10 top-[26%] bottom-[27%]">
          <svg aria-hidden="true" viewBox="0 0 310 420" preserveAspectRatio="none" className="rl-respirar absolute inset-0 size-full">
            <path d="M2 50V2h48M260 2h48v48M308 370v48h-48M50 418H2v-48" fill="none" stroke="#F2B544" strokeWidth="4" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          </svg>
          <div className="rl-linea" />
        </div>

        <div className="absolute inset-x-5 top-[max(20px,env(safe-area-inset-top))] flex items-center justify-between">
          <Link to="/finca" aria-label="Cerrar cámara" className="flex size-11 items-center justify-center rounded-full bg-bosque/70">
            <Icono nombre="cerrar" grosor={2.4} />
          </Link>
          <label className="flex h-11 items-center gap-2 rounded-full bg-bosque/75 pr-1.5 pl-4 text-sm font-semibold">
            Lote
            <select
              value={lote}
              onChange={(e) => setLote(Number(e.target.value))}
              className="h-[34px] rounded-full bg-ambar px-2.5 font-bold text-[#1a1206]"
            >
              {LOTES.map((l) => (
                <option key={l} value={l}>Lote {l}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="absolute inset-x-0 top-[calc(max(20px,env(safe-area-inset-top))+56px)] flex flex-col items-center gap-2 px-4">
          <span className="rounded-xl bg-bosque/80 px-4 py-2.5 text-center text-sm font-medium">
            {analizando ? 'Analizando la foto…' : GUIA[tipo]}
          </span>
          <InsigniaDemo modo={modo} />
          {!enVivo && !analizando && (
            <span className="rounded-xl bg-bosque/80 px-3 py-1.5 text-center text-xs text-medio">
              Imagen de referencia. Toca el botón para abrir la cámara o elegir una foto.
            </span>
          )}
        </div>

        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center gap-4 rounded-t-[28px] bg-bosque px-6 pt-5 pb-[max(28px,env(safe-area-inset-bottom))]">
          {error && (
            <div className="w-full">
              <Error mensaje={error} />
            </div>
          )}
          <div role="group" aria-label="Qué vas a escanear" className="flex rounded-full bg-[#12291d] p-1">
            {[
              ['roya', 'Hoja · roya'],
              ['maduracion', 'Racimo · maduración'],
            ].map(([id, texto]) => (
              <button
                key={id}
                type="button"
                aria-pressed={tipo === id}
                onClick={() => setTipo(id)}
                className={`h-11 rounded-full px-4 text-sm whitespace-nowrap ${tipo === id ? 'bg-ambar font-bold text-[#1a1206]' : 'font-semibold text-claro'}`}
              >
                {texto}
              </button>
            ))}
          </div>
          <div className="flex w-full items-center justify-between">
            <button
              type="button"
              aria-label="Subir foto de la galería"
              disabled={analizando}
              onClick={() => {
                galeria.current.removeAttribute('capture')
                galeria.current.click()
              }}
              className="flex size-[52px] items-center justify-center rounded-[14px] border border-[#2c4f3b] bg-tarjeta disabled:opacity-60"
            >
              <Icono nombre="galeria" tam={22} />
            </button>
            <button
              type="button"
              aria-label="Tomar foto y analizar"
              disabled={analizando}
              onClick={disparar}
              className="flex size-[84px] items-center justify-center rounded-full border-4 border-ambar disabled:opacity-60"
            >
              <span className={`size-16 rounded-full bg-ambar ${analizando ? 'rl-respirar' : ''}`} />
            </button>
            <Link to="/finca" aria-label="Ver Mi finca" className="flex size-[52px] items-center justify-center rounded-[14px] border border-[#2c4f3b] bg-tarjeta">
              <Icono nombre="casa" tam={22} />
            </Link>
          </div>
        </div>

        <input
          ref={galeria}
          type="file"
          accept="image/*"
          capture="environment"
          hidden
          onChange={(e) => {
            const archivo = e.target.files?.[0]
            e.target.value = ''
            e.target.setAttribute('capture', 'environment')
            if (archivo) enviar(archivo)
          }}
        />
      </div>
    </div>
  )
}
