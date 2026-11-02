import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { obtenerEjemplos, obtenerEstado } from '../api.js'

export const LOTES = [1, 2, 3, 4]

export function Logo({ tam = 34 }) {
  return (
    <svg aria-hidden="true" width={tam} height={tam} viewBox="0 0 34 34">
      <circle cx="17" cy="17" r="15" fill="none" stroke="#F2B544" strokeWidth="2" />
      <ellipse cx="17" cy="17" rx="7" ry="10" fill="#E5483B" />
      <path d="M17 8 C 14 14 20 20 17 26" stroke="#7A1E17" strokeWidth="2" fill="none" />
    </svg>
  )
}

const TRAZOS = {
  atras: <path d="M15 18l-6-6 6-6" />,
  cerrar: <path d="M18 6 6 18M6 6l12 12" />,
  mas: <path d="M12 5v14M5 12h14" />,
  casa: <path d="M3 10l9-7 9 7v10a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1Z" />,
  hoja: <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />,
  cerezas: (
    <>
      <circle cx="8" cy="14" r="4" />
      <circle cx="16" cy="14" r="4" />
      <circle cx="12" cy="8" r="4" />
    </>
  ),
  camara: (
    <>
      <path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  galeria: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21" />
    </>
  ),
  suelo: <path d="M3 17h18M5 21h14M12 17V7M12 11c-3 0-5-2-5-5 3 0 5 2 5 5ZM12 9c2.5 0 4-1.6 4-4-2.5 0-4 1.6-4 4Z" />,
  alerta: <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />,
  check: <path d="M5 12l5 5L20 7" />,
  chat: <path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />,
  enviar: <path d="M12 19V5M5 12l7-7 7 7" />,
  calendario: (
    <>
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </>
  ),
}

export function Icono({ nombre, tam = 20, className, grosor = 2 }) {
  return (
    <svg
      aria-hidden="true"
      width={tam}
      height={tam}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={grosor}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {TRAZOS[nombre]}
    </svg>
  )
}

export function useModo() {
  const [modo, setModo] = useState(null)
  useEffect(() => {
    obtenerEstado()
      .then((e) => setModo(e.modo))
      .catch(() => setModo(null))
  }, [])
  return modo
}

export function InsigniaDemo({ modo }) {
  if (modo !== 'demo') return null
  return (
    <span
      title="Segmentación local por color y textos de ejemplo. No usa SAM ni Muse."
      className="inline-flex items-center gap-2 rounded-lg border border-ambar/60 bg-ambar/10 px-2.5 py-1.5 font-mono text-[11px] font-semibold tracking-wide whitespace-nowrap text-ambar-claro"
    >
      <span className="size-1.5 rounded-full bg-ambar" />
      MODO DEMO · SIN SAM NI MUSE
    </span>
  )
}

export function Tarjeta({ titulo, children, className = '' }) {
  return (
    <div className={`flex flex-col gap-2 rounded-2xl border border-borde bg-tarjeta px-5 py-4 ${className}`}>
      {titulo && <h2 className="font-sora text-[15px] font-semibold text-ambar">{titulo}</h2>}
      {children}
    </div>
  )
}

export function Error({ mensaje, alReintentar }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl border border-cereza/60 bg-[#2a0f0d] px-5 py-4">
      <Icono nombre="alerta" className="mt-0.5 flex-none text-[#ff8a7a]" />
      <div className="flex flex-col items-start gap-2">
        <span className="font-sora text-[15px] font-semibold text-[#ffd3cc]">No se pudo completar</span>
        <span className="text-sm leading-relaxed text-[#f2d6d1]">{mensaje}</span>
        {alReintentar && (
          <button onClick={alReintentar} className="min-h-11 text-sm font-semibold text-ambar underline underline-offset-4">
            Intentar de nuevo
          </button>
        )}
      </div>
    </div>
  )
}

export function BarraPantalla({ titulo, subtitulo, children, modo }) {
  return (
    <header className="flex flex-none flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-[#1b3428] px-4 py-3 lg:min-h-[76px] lg:px-9">
      <div className="flex min-w-0 items-center gap-4">
        <Link
          to="/finca"
          aria-label="Volver a Mi finca"
          className="flex size-11 flex-none items-center justify-center rounded-xl border border-[#23463a] text-texto hover:border-ambar"
        >
          <Icono nombre="atras" />
        </Link>
        <div className="flex min-w-0 flex-col gap-0.5">
          <h1 className="font-sora text-xl font-extrabold lg:text-[22px]">{titulo}</h1>
          <span className="truncate text-[13px] text-suave">{subtitulo}</span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2.5">
        <InsigniaDemo modo={modo} />
        {children}
      </div>
    </header>
  )
}

export function SelectorLote({ valor, alCambiar, deshabilitado }) {
  return (
    <label className="flex items-center gap-2 text-sm text-medio">
      Lote
      <select
        value={valor}
        disabled={deshabilitado}
        onChange={(e) => alCambiar(Number(e.target.value))}
        className="h-11 rounded-xl border border-borde-fuerte bg-tarjeta px-3 font-semibold text-texto disabled:opacity-60"
      >
        {LOTES.map((l) => (
          <option key={l} value={l}>
            Lote {l}
          </option>
        ))}
      </select>
    </label>
  )
}

/** Tamaño que ocupa una foto dentro de su contenedor, sin recortarla. */
export function useEncaje(ancho, alto) {
  const ref = useRef(null)
  const [tam, setTam] = useState({ width: 0, height: 0 })
  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !ancho || !alto) return
    const medir = () => {
      const escala = Math.min(el.clientWidth / ancho, el.clientHeight / alto)
      setTam({ width: ancho * escala, height: alto * escala })
    }
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(el)
    return () => observador.disconnect()
  }, [ancho, alto])
  return [ref, tam]
}

export function Foto({ src, ancho, alto, alt, children }) {
  const [ref, tam] = useEncaje(ancho, alto)
  return (
    <div ref={ref} className="absolute inset-0 flex items-center justify-center overflow-hidden">
      <img src={src} alt="" aria-hidden="true" className="absolute inset-0 size-full scale-110 object-cover opacity-35 blur-2xl" />
      <div className="relative" style={tam}>
        <img src={src} alt={alt} draggable={false} className="block size-full select-none" />
        {children}
      </div>
    </div>
  )
}

export const AVISO_FOTOS = {
  real: 'Sus fotos se envían a los modelos de Meta para el análisis y se guardan hasta 30 días para su historial. Puede borrarlas en Mi finca.',
  demo: 'En modo demo, sus fotos se analizan en este servidor sin enviarlas a Meta. Se guardan hasta 30 días para su historial y puede borrarlas en Mi finca.',
  desconocido: 'Sus fotos se guardan hasta 30 días para su historial. Puede borrarlas en Mi finca.',
}

export function CreditoFoto({ foto }) {
  if (!foto) return null
  const texto = `Foto de ejemplo: ${foto.credito}`
  return foto.url ? (
    <a href={foto.url} target="_blank" rel="noreferrer" className="text-xs text-suave underline hover:text-texto">{texto}</a>
  ) : (
    <span className="text-xs text-suave">{texto}</span>
  )
}

/** Galería para probar la app sin tener un cafetal cerca. */
export function GaleriaEjemplos({ tipo, activo, deshabilitado, alElegir }) {
  const [ejemplos, setEjemplos] = useState([])
  useEffect(() => {
    obtenerEjemplos(tipo).then(setEjemplos).catch(() => setEjemplos([]))
  }, [tipo])
  if (ejemplos.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold text-claro">Pruebe con una foto de ejemplo</h3>
      <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {ejemplos.map((e) => (
          <li key={e.slug}>
            <button
              type="button"
              disabled={deshabilitado}
              onClick={() => alElegir(e)}
              title={e.credito}
              className={`flex w-full flex-col overflow-hidden rounded-xl border bg-tarjeta text-left hover:border-ambar disabled:opacity-60 ${activo === e.slug ? 'border-ambar' : 'border-borde-fuerte'}`}
            >
              <img src={e.imagen_url} alt="" loading="lazy" className="aspect-[4/3] w-full object-cover" />
              <span className="flex flex-col px-2.5 py-2">
                <span className="text-[13px] font-semibold text-texto">{e.titulo}</span>
                <span className="font-mono text-[10px] text-suave">{e.generada ? 'GENERADA CON IA' : 'FOTO REAL'}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function BotonesFoto({ alElegir, deshabilitado, tipo }) {
  const entrada = useRef(null)
  return (
    <>
      <input
        ref={entrada}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          const archivo = e.target.files?.[0]
          e.target.value = ''
          if (archivo) alElegir(archivo)
        }}
      />
      <button
        disabled={deshabilitado}
        onClick={() => entrada.current.click()}
        className="flex h-[52px] flex-1 items-center justify-center gap-2 rounded-xl border border-borde-fuerte px-4 font-semibold text-texto hover:border-ambar disabled:opacity-60"
      >
        <Icono nombre="galeria" />
        Subir foto
      </button>
      <Link
        to={`/camara?tipo=${tipo}`}
        className="flex h-[52px] flex-1 items-center justify-center gap-2 rounded-xl border border-borde-fuerte px-4 font-semibold whitespace-nowrap text-texto hover:border-ambar"
      >
        <Icono nombre="camara" />
        Usar cámara
      </Link>
    </>
  )
}

/** Atribución de los modelos usados por la app. */
export function ConstruidoConMeta({ className = '' }) {
  return (
    <span className={`inline-flex flex-wrap items-center gap-x-1.5 ${className}`}>
      <img src="/img/meta-symbol.svg" alt="" className="mr-1 h-[16px] w-auto flex-none" />
      Impulsado por IA de Meta: <b className="font-semibold text-texto">SAM 3.1</b> y <b className="font-semibold text-texto">Muse Spark</b>
    </span>
  )
}

export function NavLateral() {
  const clase = ({ isActive }) =>
    `flex h-[46px] items-center gap-3 rounded-xl px-3.5 ${
      isActive ? 'bg-activo font-semibold text-white' : 'text-medio hover:bg-[#12291d] hover:text-white'
    }`
  return (
    <aside className="hidden w-[248px] flex-none flex-col gap-1.5 border-r border-[#1b3428] bg-lateral px-[18px] py-7 lg:flex">
      <Link to="/" className="flex items-center gap-2.5 px-2.5 pb-6 font-sora text-xl font-extrabold text-white">
        <Logo tam={30} />
        RoyaLens
        <img src="/img/meta-symbol.svg" alt="" className="ml-auto h-[14px] w-auto" />
      </Link>
      <NavLink to="/finca" className={clase}>
        <Icono nombre="casa" />
        Mi finca
      </NavLink>
      <NavLink to="/roya" className={clase}>
        <Icono nombre="hoja" />
        Escáner de roya
      </NavLink>
      <NavLink to="/maduracion" className={clase}>
        <Icono nombre="cerezas" />
        Maduración
      </NavLink>
      <NavLink to="/asistente" className={clase}>
        <Icono nombre="chat" />
        Asistente
      </NavLink>
      <div className="flex h-[46px] items-center gap-3 px-3.5 text-[#8aa596]">
        <Icono nombre="suelo" />
        Suelo · pronto
      </div>
      <div className="flex-1" />
      <ConstruidoConMeta className="px-2.5 pb-3 text-xs leading-relaxed text-suave" />
      <Link to="/camara" className="flex flex-col gap-1 rounded-xl border border-[#23463a] bg-[#12291d] p-4 hover:border-ambar">
        <span className="font-semibold text-white">Escanee desde el cafetal</span>
        <span className="text-[13px] text-suave">Abra RoyaLens en su celular</span>
      </Link>
    </aside>
  )
}

export function NavInferior() {
  const clase = ({ isActive }) =>
    `flex min-h-14 flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
      isActive ? 'text-ambar' : 'text-medio'
    }`
  return (
    <nav aria-label="Principal" className="sticky bottom-0 z-20 flex border-t border-[#1b3428] bg-lateral pb-[env(safe-area-inset-bottom)] lg:hidden">
      <NavLink to="/finca" className={clase}>
        <Icono nombre="casa" />
        Mi finca
      </NavLink>
      <NavLink to="/roya" className={clase}>
        <Icono nombre="hoja" />
        Roya
      </NavLink>
      <NavLink to="/camara" className={clase}>
        <Icono nombre="camara" />
        Cámara
      </NavLink>
      <NavLink to="/maduracion" className={clase}>
        <Icono nombre="cerezas" />
        Maduración
      </NavLink>
      <NavLink to="/asistente" className={clase}>
        <Icono nombre="chat" />
        Asistente
      </NavLink>
    </nav>
  )
}

export function fechaCorta(iso) {
  return new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' }).format(new Date(iso))
}
