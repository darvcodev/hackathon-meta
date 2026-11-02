import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { analizar, analizarEjemplo, obtenerEscaneo } from '../api.js'
import { AVISO_FOTOS, BarraPantalla, BotonesFoto, CreditoFoto, Error, Foto, GaleriaEjemplos, Icono, NavInferior, SelectorLote, Tarjeta, useModo } from '../components/ui.jsx'

const FOTO_EJEMPLO = '/img/maduracion.jpg'
const ESTADOS = {
  verde: { nombre: 'Verde', color: '#7FB04A' },
  pinton: { nombre: 'Pintón', color: '#E9B23B' },
  maduro: { nombre: 'Maduro', color: '#E5483B' },
  sobremaduro: { nombre: 'Sobremaduro', color: '#A23A5E' },
}

function Filtros({ filtro, setFiltro }) {
  const opciones = [['todas', 'Todas', '#EAF2EC'], ...Object.entries(ESTADOS).map(([k, v]) => [k, v.nombre, v.color])]
  return (
    <div role="group" aria-label="Filtrar por estado" className="flex flex-wrap gap-2">
      {opciones.map(([id, nombre, color]) => {
        const activo = filtro === id
        return (
          <button
            key={id}
            type="button"
            aria-pressed={activo}
            onClick={() => setFiltro(id)}
            className={`inline-flex h-11 items-center gap-2 rounded-full border px-4 text-sm font-semibold ${
              activo ? 'border-ambar bg-ambar text-[#1a1206]' : 'border-[#2c4f3b] bg-tarjeta text-texto hover:border-ambar'
            }`}
          >
            <span className="size-2.5 rounded-full" style={{ background: color }} />
            {nombre}
          </button>
        )
      })}
    </div>
  )
}

function Detecciones({ escaneo, filtro }) {
  return (
    <section aria-label="Racimo analizado" className="relative min-h-[360px] overflow-hidden rounded-3xl border border-borde bg-visor">
      <Foto src={escaneo.imagen_url} ancho={escaneo.ancho} alto={escaneo.alto} alt="Racimo de café analizado">
        {escaneo.detecciones.map((d, i) => {
          const estado = ESTADOS[d.estado]
          const visible = filtro === 'todas' || filtro === d.estado
          return (
            <motion.div
              key={d.id}
              title={estado.nombre}
              initial={{ opacity: 0, scale: 1.5 }}
              animate={{ opacity: visible ? 1 : 0.15, scale: 1 }}
              transition={{ delay: filtro === 'todas' ? 0.15 + i * 0.05 : 0, duration: 0.3 }}
              className="absolute rounded-full border-[3px]"
              style={{
                left: `${d.caja[0] * 100}%`,
                top: `${d.caja[1] * 100}%`,
                width: `${(d.caja[2] - d.caja[0]) * 100}%`,
                height: `${(d.caja[3] - d.caja[1]) * 100}%`,
                borderColor: '#FFFFFF',
                boxShadow: `0 0 0 3px ${estado.color}`,
              }}
            />
          )
        })}
      </Foto>
      <span className="absolute top-4 left-4 rounded-lg bg-bosque/85 px-3 py-1.5 font-mono text-xs text-ambar-claro">
        {escaneo.medicion.total} CEREZAS DETECTADAS
      </span>
    </section>
  )
}

function Resultado({ escaneo, modo }) {
  const { medicion, recomendacion, interpretacion, avisos } = escaneo
  const total = medicion.total
  const valida = medicion.valida !== false
  return (
    <section aria-label="Resultado de maduración" className="flex min-h-0 flex-col gap-3 lg:overflow-y-auto">
      {avisos.map((aviso) => (
        <div key={aviso} role="status" className="flex flex-none items-start gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3 text-sm text-ambar-claro">
          <Icono nombre="alerta" className="mt-0.5 flex-none" />
          {aviso}
        </div>
      ))}
      {!valida && (
        <div className="flex flex-none flex-col gap-1 rounded-[22px] border border-borde bg-tarjeta px-6 py-5">
          <span className="font-sora text-xl font-extrabold">Sin conteo</span>
          <span className="text-sm text-medio">Esta foto no se cuenta en el historial del lote.</span>
        </div>
      )}
      {valida && <div className="flex flex-none flex-col gap-3.5 rounded-[22px] border border-borde bg-tarjeta p-6">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-sm text-suave">Cerezas en punto de cosecha</span>
          <span className="font-mono text-xs text-medio">MADURAS / TOTAL</span>
        </div>
        <div className="font-sora text-6xl leading-none font-extrabold text-texto">{medicion.porcentaje_maduro}%</div>
        {total > 0 && (
          <div className="flex h-[18px] gap-0.5 overflow-hidden rounded-full bg-borde">
            {Object.entries(ESTADOS).map(([k, v]) =>
              medicion.conteo[k] > 0 ? (
                <motion.div
                  key={k}
                  title={`${v.nombre}: ${medicion.conteo[k]}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${(100 * medicion.conteo[k]) / total}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  style={{ background: v.color }}
                />
              ) : null,
            )}
          </div>
        )}
        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
          {Object.entries(ESTADOS).map(([k, v]) => (
            <div key={k} className="flex flex-col gap-1 rounded-xl bg-visor px-3 py-2.5">
              <span className="flex items-center gap-1.5 text-xs text-medio">
                <span className="size-2.5 flex-none rounded-full" style={{ background: v.color }} />
                {v.nombre}
              </span>
              <span className="font-sora text-[22px] font-extrabold">{medicion.conteo[k]}</span>
            </div>
          ))}
        </div>
      </div>}
      {valida && <div className="flex flex-none items-center gap-4 rounded-[20px] border border-[#7a2a22] bg-[#2a0f0d] px-5 py-4">
        <Icono nombre="calendario" tam={36} className="flex-none text-[#ff8a7a]" />
        <div className="flex flex-col gap-1">
          <span className="font-sora text-[17px] font-semibold text-[#ffd3cc]">{recomendacion.titulo}</span>
          <span className="text-sm leading-relaxed text-[#f2d6d1]">{recomendacion.texto}</span>
        </div>
      </div>}
      {interpretacion ? (
        <>
          <Tarjeta titulo="Lo que se ve" className="flex-none">
            <p className="text-[15px] leading-relaxed text-claro">{interpretacion.lo_que_se_ve || 'Sin descripción.'}</p>
          </Tarjeta>
          {interpretacion.recomendacion && (
            <Tarjeta titulo="Qué hacer" className="flex-none">
              <p className="text-[15px] leading-relaxed text-claro">{interpretacion.recomendacion}</p>
            </Tarjeta>
          )}
          {interpretacion.consejo_foto && <p className="flex-none text-sm text-medio">{interpretacion.consejo_foto}</p>}
        </>
      ) : (
        <Tarjeta titulo="Por qué importa" className="flex-none">
          <p className="text-[15px] leading-relaxed text-claro">
            Recoger cerezas verdes o sobremaduras baja la calidad en taza. Contar por racimo ayuda a planear los pases de cosecha y los recolectores.
          </p>
        </Tarjeta>
      )}
      <div className="flex-1" />
      <Link to={`/asistente?escaneo=${escaneo.id}&lote=${escaneo.lote}`} className="flex h-11 flex-none items-center justify-center gap-2 rounded-xl border border-borde-fuerte px-4 text-sm font-semibold hover:border-ambar">
        <Icono nombre="chat" tam={18} />
        Preguntar sobre este resultado
      </Link>
      <div className="flex flex-none flex-wrap gap-3">
        <Link to="/finca" className="flex h-[52px] flex-1 items-center justify-center rounded-xl bg-ambar px-4 font-bold whitespace-nowrap text-[#1a1206] hover:bg-[#ffc85e]">
          Ver en Mi finca · Lote {escaneo.lote}
        </Link>
        <Link to="/maduracion" className="flex h-[52px] flex-1 items-center justify-center rounded-xl border border-borde-fuerte px-4 font-semibold whitespace-nowrap hover:border-ambar">
          Escanear otro racimo
        </Link>
      </div>
      <CreditoFoto foto={escaneo.foto_ejemplo} />
      {modo === 'demo' && <p className="flex-none text-xs leading-relaxed text-suave">Conteo local por color para probar la interfaz. Puede fallar con cerezas tapadas o verdes sobre hojas.</p>}
    </section>
  )
}

export default function Maduracion() {
  const { id } = useParams()
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const modo = useModo()
  const [escaneo, setEscaneo] = useState(null)
  const [error, setError] = useState(null)
  const [analizando, setAnalizando] = useState(false)
  const [vista, setVista] = useState(FOTO_EJEMPLO)
  const [filtro, setFiltro] = useState('todas')
  const [lote, setLote] = useState(Number(parametros.get('lote')) || 2)
  const [activo, setActivo] = useState(null)

  useEffect(() => {
    setError(null)
    setFiltro('todas')
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

  async function procesar(archivo) {
    setVista(URL.createObjectURL(archivo))
    setError(null)
    setAnalizando(true)
    try {
      const resultado = await analizar('maduracion', archivo, lote)
      navegar(`/maduracion/${resultado.id}`)
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
      navegar(`/maduracion/${resultado.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setAnalizando(false)
      setActivo(null)
    }
  }

  const subtitulo = escaneo ? `Lote ${escaneo.lote} · resultado guardado` : 'Cuenta las cerezas por estado'
  return (
    <div className="flex min-h-dvh flex-col lg:h-dvh lg:overflow-hidden">
      <BarraPantalla titulo="Maduración del grano" subtitulo={subtitulo} modo={modo}>
        {escaneo && <Filtros filtro={filtro} setFiltro={setFiltro} />}
      </BarraPantalla>
      {id && error ? (
        <div className="flex-1 p-4 lg:px-9 lg:py-6">
          <Error mensaje={error} />
        </div>
      ) : id && !escaneo ? (
        <p role="status" className="p-9 text-medio">Cargando el escaneo…</p>
      ) : (
        <div className="grid min-h-0 flex-1 gap-6 p-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] lg:px-9 lg:py-6">
          {escaneo ? (
            <>
              <Detecciones escaneo={escaneo} filtro={filtro} />
              <Resultado escaneo={escaneo} modo={modo} />
            </>
          ) : (
            <>
              <section className="relative min-h-[360px] overflow-hidden rounded-3xl border border-borde bg-visor">
                <img src={vista} alt={analizando ? 'Foto que se está analizando' : 'Racimo de café'} className="absolute inset-0 size-full object-contain" />
                {analizando && <div className="rl-linea" />}
                <span className="absolute top-4 left-4 rounded-lg bg-bosque/85 px-3 py-1.5 font-mono text-xs text-ambar-claro">
                  {analizando ? 'ANALIZANDO…' : 'IMAGEN GENERADA CON IA'}
                </span>
              </section>
              <section className="flex flex-col gap-4 lg:overflow-y-auto">
                <div className="flex flex-col gap-2">
                  <h2 className="font-sora text-2xl font-extrabold">Escanee un racimo</h2>
                  <p className="leading-relaxed text-medio">Tome la foto de cerca y de frente. La app cuenta las cerezas por estado y le dice si ya conviene recolectar.</p>
                </div>
                {error && <Error mensaje={error} />}
                <SelectorLote valor={lote} alCambiar={setLote} deshabilitado={analizando} />
                <div className="flex flex-wrap gap-3">
                  <BotonesFoto tipo="maduracion" alElegir={procesar} deshabilitado={analizando} />
                </div>
                <GaleriaEjemplos tipo="maduracion" activo={activo} deshabilitado={analizando} alElegir={usarEjemplo} />
                <p className="text-xs leading-relaxed text-suave">{AVISO_FOTOS[modo] ?? AVISO_FOTOS.desconocido}</p>
              </section>
            </>
          )}
        </div>
      )}
      <NavInferior />
    </div>
  )
}
