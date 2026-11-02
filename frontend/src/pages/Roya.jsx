import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { analizar, analizarEjemplo, obtenerEscaneo } from '../api.js'
import { AVISO_FOTOS, BarraPantalla, BotonesFoto, CreditoFoto, Error, Foto, GaleriaEjemplos, Icono, NavInferior, SelectorLote, Tarjeta, useModo } from '../components/ui.jsx'

const FOTO_EJEMPLO = '/img/escaner-roya.jpg'
const PASOS = ['Hoja recortada', 'Lesiones segmentadas', 'Área medida', 'Explicado']
const LARGO_ARCO = 219.9
const DAE_CENICAFE = 'https://biblioteca.cenicafe.org/bitstream/10778/4244/1/avt0498.pdf'

export function colorNivel(nivel) {
  return (
    {
      'Sin roya visible': '#5FCB7E',
      Leve: '#E9B23B',
      Moderada: '#F0A04B',
      Alta: '#E3632D',
      Severa: '#E5483B',
    }[nivel] ?? '#A3BBAA'
  )
}

function Pasos({ activo }) {
  return (
    <ol aria-label="Pasos del análisis" className="hidden gap-2 text-[13px] xl:flex">
      {PASOS.map((paso, i) => {
        const hecho = activo === null || i < activo
        const actual = i === activo
        return (
          <li
            key={paso}
            className={`flex h-9 items-center gap-2 rounded-full px-3.5 ${
              hecho ? 'bg-[#10291c] text-[#c8f2d3]' : actual ? 'rl-respirar bg-[#2a220e] text-ambar-claro' : 'bg-tarjeta text-suave'
            }`}
          >
            {hecho && <Icono nombre="check" tam={16} grosor={3} className="text-exito" />}
            {paso}
          </li>
        )
      })}
    </ol>
  )
}

function Comparador({ escaneo }) {
  const [corte, setCorte] = useState(55)
  const area = useRef(null)
  if (!escaneo.medicion.valida) {
    return (
      <section aria-label="Foto enviada" className="relative min-h-[320px] flex-1 overflow-hidden rounded-3xl border border-borde bg-visor">
        <Foto src={escaneo.imagen_url} ancho={escaneo.ancho} alto={escaneo.alto} alt="Foto enviada, sin medición" />
      </section>
    )
  }
  const moverA = (e) => {
    const r = area.current.getBoundingClientRect()
    setCorte(Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100)))
  }
  return (
    <section aria-label="Comparación de la hoja" className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="relative min-h-[320px] flex-1 overflow-hidden rounded-3xl border border-borde bg-visor">
        <Foto src={escaneo.imagen_url} ancho={escaneo.ancho} alto={escaneo.alto} alt="Foto original de la hoja">
          <div
            ref={area}
            className="absolute inset-0 cursor-ew-resize touch-none"
            onPointerDown={(e) => {
              e.currentTarget.setPointerCapture(e.pointerId)
              moverA(e)
            }}
            onPointerMove={(e) => e.buttons && moverA(e)}
          >
            <img
              src={escaneo.overlay_url}
              alt="Análisis: hoja contorneada en verde y lesiones resaltadas en naranja"
              draggable={false}
              className="absolute inset-0 size-full select-none"
              style={{ clipPath: `inset(0 ${100 - corte}% 0 0)` }}
            />
            <div className="absolute inset-y-0 overflow-hidden" style={{ left: 0, width: `${corte}%` }}>
              {escaneo.detecciones.slice(0, 40).map((d, i) => (
                <motion.span
                  key={d.id}
                  initial={{ opacity: 0, scale: 1.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.25 + i * 0.05, duration: 0.3 }}
                  className="pointer-events-none absolute rounded-sm border border-[#ffeb3b]"
                  style={{
                    left: `${(d.caja[0] * 100 * 100) / Math.max(corte, 0.01)}%`,
                    top: `${d.caja[1] * 100}%`,
                    width: `${((d.caja[2] - d.caja[0]) * 100 * 100) / Math.max(corte, 0.01)}%`,
                    height: `${(d.caja[3] - d.caja[1]) * 100}%`,
                  }}
                />
              ))}
            </div>
            <div className="absolute inset-y-0 w-[3px] -translate-x-1/2 bg-ambar" style={{ left: `${corte}%` }}>
              <span className="absolute top-1/2 left-1/2 flex size-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-ambar font-mono text-sm font-bold text-[#1a1206]">
                ↔
              </span>
            </div>
          </div>
        </Foto>
        <span className="absolute top-4 left-4 rounded-lg bg-bosque/85 px-3 py-1.5 font-mono text-xs text-ambar-claro">ANÁLISIS</span>
        <span className="absolute top-4 right-4 rounded-lg bg-bosque/85 px-3 py-1.5 font-mono text-xs">FOTO ORIGINAL</span>
      </div>
      <label className="flex flex-none items-center gap-4 text-sm text-medio">
        <span className="flex-none">Deslice para comparar</span>
        <input
          type="range"
          min="0"
          max="100"
          value={corte}
          onChange={(e) => setCorte(Number(e.target.value))}
          className="h-7 w-full accent-ambar"
        />
      </label>
    </section>
  )
}

function Medidor({ medicion }) {
  const color = colorNivel(medicion.nivel)
  const fraccion = Math.min(medicion.porcentaje / 50, 1)
  return (
    <div className="relative h-[100px] w-[170px] flex-none">
      <svg role="img" aria-label={`Medidor de severidad en ${medicion.porcentaje} por ciento`} width="170" height="100" viewBox="0 0 170 100">
        <path d="M15 90 A70 70 0 0 1 155 90" fill="none" stroke="#1F3A2B" strokeWidth="14" strokeLinecap="round" />
        <motion.path
          d="M15 90 A70 70 0 0 1 155 90"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={LARGO_ARCO}
          initial={{ strokeDashoffset: LARGO_ARCO }}
          animate={{ strokeDashoffset: LARGO_ARCO * (1 - fraccion) }}
          transition={{ duration: 1.4, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center font-sora text-3xl font-extrabold text-texto">{medicion.porcentaje}%</div>
    </div>
  )
}

function Resultado({ escaneo, modo }) {
  const { medicion, interpretacion, avisos } = escaneo
  const datos = [`${medicion.lesiones} LESIONES`]
  if (medicion.confianza !== null) datos.push(`CONFIANZA SAM ${medicion.confianza}`)
  const muse = []
  if (interpretacion.signos_de_roya != null) muse.push(`Signos de roya: ${interpretacion.signos_de_roya ? 'sí' : 'no'}`)
  if (interpretacion.calidad_foto) muse.push(`Calidad de la foto: ${interpretacion.calidad_foto}`)
  if (interpretacion.cara_visible === 'haz' || interpretacion.cara_visible === 'enves') muse.push(`Cara visible: ${interpretacion.cara_visible === 'enves' ? 'envés' : 'haz'}`)
  return (
    <section aria-label="Resultado" className="flex min-h-0 flex-col gap-3 lg:overflow-y-auto">
      {avisos.map((aviso) => (
        <div key={aviso} role="status" className="flex flex-none items-start gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3 text-sm text-ambar-claro">
          <Icono nombre="alerta" className="mt-0.5 flex-none" />
          {aviso}
        </div>
      ))}
      {medicion.valida ? (
        <div className="flex flex-none flex-wrap items-center gap-5 rounded-[22px] border border-borde bg-tarjeta px-6 py-5">
          <Medidor medicion={medicion} />
          <div className="flex flex-col gap-1.5">
            <span className="text-[13px] text-suave">Hoja afectada · estimado con máscaras de SAM</span>
            <span className="flex items-center gap-2 font-sora text-2xl font-extrabold">
              <span className="size-3 rounded-full" style={{ background: colorNivel(medicion.nivel) }} />
              {medicion.nivel}
            </span>
            <span className="font-mono text-xs text-medio">{datos.join(' · ')}</span>
            {medicion.clase_dae !== null && (
              <span className="text-xs leading-relaxed text-medio">
                Equivale a la clase de {medicion.clase_dae}% del{' '}
                <a href={DAE_CENICAFE} target="_blank" rel="noreferrer" className="underline hover:text-texto">diagrama de Cenicafé</a>. Nivel orientativo.
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="flex flex-none flex-col gap-1 rounded-[22px] border border-borde bg-tarjeta px-6 py-5">
          <span className="font-sora text-xl font-extrabold">Sin medición</span>
          <span className="text-sm text-medio">Esta foto no se cuenta en el historial del lote.</span>
        </div>
      )}
      {muse.length > 0 && (
        <div className="flex flex-none flex-wrap gap-2 text-xs text-claro">
          {muse.map((m) => (
            <span key={m} className="rounded-full border border-borde bg-tarjeta px-3 py-1.5">{m}</span>
          ))}
        </div>
      )}
      <Tarjeta titulo="Lo que se ve" className="flex-none">
        <p className="text-[15px] leading-relaxed text-claro">{interpretacion.lo_que_se_ve || 'Sin descripción.'}</p>
      </Tarjeta>
      <Tarjeta titulo="Qué hacer" className="flex-none">
        <p className="text-[15px] leading-relaxed text-claro">{interpretacion.recomendacion || 'Sin recomendación.'}</p>
      </Tarjeta>
      {interpretacion.otras_causas.length > 0 && (
        <div className="flex-none rounded-2xl border border-dashed border-[#2f5242] px-5 py-3.5 text-sm text-medio">
          Podría confundirse con: <b className="text-texto">{interpretacion.otras_causas.join(', ')}</b>.
        </div>
      )}
      {interpretacion.consejo_foto && <p className="flex-none text-sm text-medio">{interpretacion.consejo_foto}</p>}
      <div className="flex-1" />
      <Link to={`/asistente?escaneo=${escaneo.id}&lote=${escaneo.lote}`} className="flex h-11 flex-none items-center justify-center gap-2 rounded-xl border border-borde-fuerte px-4 text-sm font-semibold hover:border-ambar">
        <Icono nombre="chat" tam={18} />
        Preguntar sobre este resultado
      </Link>
      <div className="flex flex-none flex-wrap gap-3">
        <Link to="/finca" className="flex h-[52px] flex-1 items-center justify-center rounded-xl bg-ambar px-4 font-bold whitespace-nowrap text-[#1a1206] hover:bg-[#ffc85e]">
          Ver en Mi finca · Lote {escaneo.lote}
        </Link>
        <Link to="/roya" className="flex h-[52px] flex-1 items-center justify-center rounded-xl border border-borde-fuerte px-4 font-semibold whitespace-nowrap hover:border-ambar">
          Escanear otra hoja
        </Link>
      </div>
      <CreditoFoto foto={escaneo.foto_ejemplo} />
      {modo === 'demo' && <p className="flex-none text-xs leading-relaxed text-suave">Medición local por color para probar la interfaz. No es un diagnóstico.</p>}
    </section>
  )
}

function Preparacion({ vista, analizando, error, lote, setLote, alElegir, alEjemplo, activo }) {
  return (
    <div className="grid min-h-0 flex-1 gap-6 p-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:px-9 lg:py-6">
      <section className="relative min-h-[360px] overflow-hidden rounded-3xl border border-borde bg-visor">
        <img src={vista} alt={analizando ? 'Foto que se está analizando' : 'Hoja de café con roya'} className="absolute inset-0 size-full object-contain" />
        {analizando && <div className="rl-linea" />}
        <span className="absolute top-4 left-4 rounded-lg bg-bosque/85 px-3 py-1.5 font-mono text-xs text-ambar-claro">
          {analizando ? 'ANALIZANDO…' : 'IMAGEN GENERADA CON IA'}
        </span>
      </section>
      <section className="flex flex-col gap-4 lg:overflow-y-auto">
        <div className="flex flex-col gap-2">
          <h2 className="font-sora text-2xl font-extrabold">Escanee una hoja</h2>
          <p className="leading-relaxed text-medio">Una sola hoja, de cerca, mostrando el envés y con buena luz. La app mide qué porcentaje está afectado.</p>
        </div>
        {error && <Error mensaje={error} />}
        <SelectorLote valor={lote} alCambiar={setLote} deshabilitado={analizando} />
        <div className="flex flex-wrap gap-3">
          <BotonesFoto tipo="roya" alElegir={alElegir} deshabilitado={analizando} />
        </div>
        <GaleriaEjemplos tipo="roya" activo={activo} deshabilitado={analizando} alElegir={alEjemplo} />
        <p className="text-xs leading-relaxed text-suave">{AVISO_FOTOS}</p>
      </section>
    </div>
  )
}

export default function Roya() {
  const { id } = useParams()
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const modo = useModo()
  const [escaneo, setEscaneo] = useState(null)
  const [error, setError] = useState(null)
  const [analizando, setAnalizando] = useState(false)
  const [vista, setVista] = useState(FOTO_EJEMPLO)
  const [lote, setLote] = useState(Number(parametros.get('lote')) || 1)
  const [paso, setPaso] = useState(0)
  const [activo, setActivo] = useState(null)

  useEffect(() => {
    setError(null)
    if (!id) {
      setEscaneo(null)
      setVista(FOTO_EJEMPLO)
      return
    }
    let vigente = true
    obtenerEscaneo(id)
      .then((e) => vigente && setEscaneo(e))
      .catch((e) => vigente && setError(e.message))
    return () => {
      vigente = false
    }
  }, [id])

  useEffect(() => {
    if (!analizando) return
    setPaso(0)
    const reloj = setInterval(() => setPaso((p) => Math.min(p + 1, PASOS.length - 1)), 900)
    return () => clearInterval(reloj)
  }, [analizando])

  async function procesar(archivo) {
    setVista(URL.createObjectURL(archivo))
    setError(null)
    setAnalizando(true)
    try {
      const resultado = await analizar('roya', archivo, lote)
      navegar(`/roya/${resultado.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setAnalizando(false)
    }
  }

  async function usarEjemplo(ejemplo) {
    setVista(ejemplo.imagen_url)
    setActivo(ejemplo.slug)
    setError(null)
    setAnalizando(true)
    try {
      const resultado = await analizarEjemplo(ejemplo.slug, lote)
      navegar(`/roya/${resultado.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setAnalizando(false)
      setActivo(null)
    }
  }

  const subtitulo = escaneo ? `Lote ${escaneo.lote} · resultado guardado` : 'Mide cuánta hoja está afectada'
  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh lg:overflow-hidden">
      <BarraPantalla titulo="Escáner de roya" subtitulo={subtitulo} modo={modo}>
        {(escaneo || analizando) && <Pasos activo={analizando ? paso : null} />}
      </BarraPantalla>
      {id && error ? (
        <div className="flex-1 p-4 lg:px-9 lg:py-6">
          <Error mensaje={error} />
        </div>
      ) : id && !escaneo ? (
        <p role="status" className="p-9 text-medio">Cargando el escaneo…</p>
      ) : escaneo ? (
        <div className="grid min-h-0 flex-1 gap-6 p-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:px-9 lg:py-6">
          <div className="flex min-h-0 flex-col">
            <Comparador escaneo={escaneo} />
          </div>
          <Resultado escaneo={escaneo} modo={modo} />
        </div>
      ) : (
        <Preparacion
          vista={vista}
          analizando={analizando}
          error={error}
          lote={lote}
          setLote={setLote}
          alElegir={procesar}
          alEjemplo={usarEjemplo}
          activo={activo}
        />
      )}
      <NavInferior />
    </div>
  )
}
