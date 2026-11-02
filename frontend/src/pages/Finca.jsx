import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { borrarMisDatos, obtenerResumen } from '../api.js'
import { Error, Icono, InsigniaDemo, NavInferior, NavLateral, fechaCorta, num } from '../components/ui.jsx'
import { colorNivel } from './Roya.jsx'

// Lotes dibujados sobre mi-finca.jpg (1513×1040), siguiendo sus caminos.
const POLIGONOS = {
  1: '0,0 720,0 765,180 800,400 775,465 640,520 300,505 0,465',
  2: '795,0 1240,130 1513,330 1513,545 1100,520 835,455 835,300',
  3: '0,510 600,545 715,560 750,700 760,850 610,1040 0,1040',
  4: '765,525 1000,525 1513,595 1513,800 1200,1040 680,1040 785,850 775,700',
}
const CENTROS = { 1: [380, 250], 2: [1130, 300], 3: [350, 780], 4: [1090, 780] }

function Indicador({ titulo, valor, detalle, tono }) {
  return (
    <div className="flex min-w-0 flex-col gap-1 rounded-2xl border border-borde bg-tarjeta px-4 py-3.5 lg:px-5">
      <span className="text-[13px] text-suave">{titulo}</span>
      <span className="font-sora text-[28px] leading-tight font-extrabold text-texto lg:text-[32px]">{valor ?? '—'}</span>
      <span className={`text-xs ${tono === 'mala' ? 'text-[#ffb4a8]' : 'text-medio'}`}>{detalle}</span>
    </div>
  )
}

function Mapa({ lotes, elegido, setElegido }) {
  return (
    <section aria-label="Mapa de lotes" className="relative flex min-h-[360px] min-w-0 flex-col overflow-hidden rounded-[20px] border border-borde bg-visor">
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 px-5 py-3.5">
        <h2 className="font-sora text-lg font-semibold">Mapa de lotes</h2>
        <div className="flex flex-wrap gap-3 text-xs text-medio">
          {[
            ['Sin escaneo', '#6F8A7A'],
            ['Sana', colorNivel('Sin roya visible')],
            ['Leve', colorNivel('Leve')],
            ['Moderada', colorNivel('Moderada')],
            ['Alta', colorNivel('Alta')],
            ['Severa', colorNivel('Severa')],
          ].map(([t, c]) => (
            <span key={t} className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-[3px]" style={{ background: c }} />
              {t}
            </span>
          ))}
        </div>
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden px-4 pb-6 [perspective:1100px]">
        <motion.div
          initial={{ rotateX: 0, opacity: 0 }}
          animate={{ rotateX: 28, opacity: 1 }}
          transition={{ duration: 1 }}
          className="relative aspect-[1513/1040] max-h-full w-full max-w-[720px] overflow-hidden rounded-xl shadow-2xl shadow-black/60"
        >
          <img src="/img/mi-finca.jpg" alt="Vista aérea de la finca con cuatro lotes de café separados por caminos" className="absolute inset-0 size-full object-cover" />
          <svg viewBox="0 0 1513 1040" preserveAspectRatio="none" className="absolute inset-0 size-full">
            {lotes.map((l) => {
              const color = l.nivel ? colorNivel(l.nivel) : '#6F8A7A'
              const activo = l.id === elegido
              return (
                <g key={l.id}>
                  <polygon
                    points={POLIGONOS[l.id]}
                    role="button"
                    tabIndex={0}
                    aria-label={`${l.nombre}${l.nivel ? `, roya ${l.roya}%, ${l.nivel}` : ', sin escaneos'}`}
                    aria-pressed={activo}
                    onClick={() => setElegido(l.id)}
                    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setElegido(l.id)}
                    fill={color}
                    fillOpacity={activo ? 0.42 : 0.2}
                    stroke={activo ? '#FFFFFF' : color}
                    strokeWidth={activo ? 7 : 4}
                    className="cursor-pointer outline-none transition-[fill-opacity] hover:fill-opacity-40 focus-visible:stroke-white"
                  />
                  <text x={CENTROS[l.id][0]} y={CENTROS[l.id][1]} textAnchor="middle" fill="#FFFFFF" stroke="#07140D" strokeWidth="8" paintOrder="stroke" className="pointer-events-none font-sora text-[48px] font-extrabold">
                    {l.nombre}
                  </text>
                </g>
              )
            })}
          </svg>
          <div className="rl-linea" />
        </motion.div>
      </div>
    </section>
  )
}

function Evolucion({ lote }) {
  const puntos = lote.evolucion
  const [foco, setFoco] = useState(null)
  if (puntos.length === 0) {
    return <p className="py-6 text-sm text-medio">Este lote todavía no tiene escaneos de roya.</p>
  }
  const A = 400, H = 130, M = 12
  const tiempos = puntos.map((p) => new Date(p.fecha).getTime())
  const [t0, t1] = [Math.min(...tiempos), Math.max(...tiempos)]
  const techo = Math.max(10, ...puntos.map((p) => p.porcentaje)) * 1.15
  const x = (t) => (t1 === t0 ? A / 2 : M + ((t - t0) / (t1 - t0)) * (A - 2 * M))
  const y = (v) => H - 6 - (v / techo) * (H - 16)
  const coords = puntos.map((p, i) => [x(tiempos[i]), y(p.porcentaje)])
  const ultimo = puntos[puntos.length - 1]
  const activo = foco ?? puntos.length - 1
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between font-mono text-xs text-medio">
        <span>{fechaCorta(puntos[activo].fecha)}</span>
        <span className="text-texto">{num(puntos[activo].porcentaje)}%</span>
      </div>
      <svg
        role="img"
        aria-label={`Roya en ${lote.nombre}: ${puntos.map((p) => `${p.porcentaje}%`).join(', ')}; último valor ${ultimo.porcentaje}%`}
        viewBox={`0 0 ${A} ${H}`}
        className="h-[120px] w-full"
        onMouseLeave={() => setFoco(null)}
      >
        {[0, 0.5, 1].map((f) => (
          <line key={f} x1="0" x2={A} y1={y(techo * f * 0.87)} y2={y(techo * f * 0.87)} stroke="#1F3A2B" />
        ))}
        <path
          d={`M${coords.map((c) => c.join(' ')).join(' L')}`}
          fill="none"
          stroke="#F0A04B"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {coords.map(([cx, cy], i) => (
          <g key={i} onMouseEnter={() => setFoco(i)}>
            <circle cx={cx} cy={cy} r="14" fill="transparent" />
            <circle cx={cx} cy={cy} r={i === activo ? 5 : 3.5} fill="#F0A04B" stroke="#0E2218" strokeWidth="2" />
          </g>
        ))}
      </svg>
    </div>
  )
}

function etiquetaEscaneo(e) {
  if (e.tipo === 'roya') return e.medicion.valida === false ? 'Sin medición' : `${num(e.medicion.porcentaje)}% · ${e.medicion.nivel}`
  return e.medicion.valida === false ? 'Sin conteo' : `${e.medicion.porcentaje_maduro}% maduro`
}

export default function Finca() {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [elegido, setElegido] = useState(null)

  const cargar = () => {
    setError(null)
    obtenerResumen().then(setDatos).catch((e) => setError(e.message))
  }
  useEffect(cargar, [])

  useEffect(() => {
    if (datos && elegido === null) setElegido(datos.alertas.find((a) => a.nivel === 'alta')?.lote ?? 1)
  }, [datos, elegido])

  const lote = datos?.lotes.find((l) => l.id === elegido)
  const i = datos?.indicadores
  const hoy = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())

  return (
    <div className="flex min-h-dvh lg:h-dvh lg:overflow-hidden">
      <NavLateral />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex min-h-0 flex-1 flex-col gap-4 p-4 lg:gap-5 lg:px-9 lg:py-6">
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div className="flex flex-col gap-1">
              <span className="font-mono text-xs tracking-[1.5px] text-ambar uppercase">{hoy}</span>
              <h1 className="font-sora text-[28px] font-extrabold lg:text-[34px]">{datos?.es_ejemplo ? 'Así se vería su finca' : 'Así está su finca hoy'}</h1>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <InsigniaDemo modo={datos?.modo} />
              <Link to="/camara" className="inline-flex h-12 items-center gap-2.5 rounded-xl bg-ambar px-5 font-bold text-[#1a1206] hover:bg-[#ffc85e]">
                <Icono nombre="mas" tam={18} grosor={2.4} />
                Nuevo escaneo
              </Link>
            </div>
          </header>

          {error && <Error mensaje={error} alReintentar={cargar} />}
          {!datos && !error && <p role="status" className="text-medio">Cargando su finca…</p>}

          {datos && (
            <>
              {datos.es_ejemplo && (
                <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3">
                  <span className="flex items-start gap-3 text-sm text-ambar-claro">
                    <Icono nombre="alerta" className="mt-0.5 flex-none" />
                    <span><b>Finca de ejemplo.</b> Estas cifras son ilustrativas, no son mediciones reales. Con su primer escaneo, este panel pasa a mostrar solo sus datos.</span>
                  </span>
                  <Link to="/roya" className="text-sm font-bold whitespace-nowrap text-ambar underline underline-offset-4">Hacer mi primer escaneo</Link>
                </div>
              )}
              {datos.hay_fotos_ejemplo && (
                <div role="status" className="flex items-start gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3 text-sm text-ambar-claro">
                  <Icono nombre="alerta" className="mt-0.5 flex-none" />
                  <span><b>Incluye fotos de ejemplo.</b> Esos resultados muestran cómo funciona la app, no el estado de su cafetal. Puede borrarlos con «Borrar mis datos» en Mi finca.</span>
                </div>
              )}
              <section aria-label="Resumen" className="grid flex-none grid-cols-2 gap-3 xl:grid-cols-4">
                <Indicador
                  titulo="Roya promedio"
                  valor={i.roya_promedio !== null ? `${num(i.roya_promedio)}%` : null}
                  detalle={i.cambio_roya !== null ? `${i.cambio_roya > 0 ? 'sube' : 'cambia'} ${num(i.cambio_roya)} pts en 2 semanas` : 'Sin datos para comparar'}
                  tono={i.cambio_roya > 0 ? 'mala' : undefined}
                />
                <Indicador
                  titulo="Cerezas maduras"
                  valor={i.maduro_promedio !== null ? `${i.maduro_promedio}%` : null}
                  detalle={i.lote_mas_maduro ? `Más avanzado: ${i.lote_mas_maduro}` : 'Sin escaneos de racimo'}
                />
                <Indicador titulo="Escaneos este mes" valor={i.escaneos_mes} detalle={`en ${datos.lotes.length} lotes`} />
                <Indicador titulo="Lotes por revisar" valor={i.lotes_por_revisar} detalle="Sin escaneo hace 7 días o más" />
              </section>

              <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
                <Mapa lotes={datos.lotes} elegido={elegido} setElegido={setElegido} />

                <section aria-label="Actividad" className="flex min-h-0 flex-col gap-3 xl:overflow-y-auto">
                  {datos.alertas.slice(0, 2).map((a) => (
                    <button
                      key={a.lote}
                      onClick={() => setElegido(a.lote)}
                      className={`flex flex-none flex-col gap-1.5 rounded-[18px] border px-4 py-3.5 text-left ${
                        a.nivel === 'alta' ? 'border-[#6b2c17] bg-[#24120c]' : 'border-borde bg-tarjeta'
                      }`}
                    >
                      <span className={`flex items-center gap-2 font-sora text-[15px] font-semibold ${a.nivel === 'alta' ? 'text-[#ffc9ae]' : 'text-ambar-claro'}`}>
                        <Icono nombre="alerta" tam={18} />
                        {a.titulo}
                      </span>
                      <span className={`text-sm leading-relaxed ${a.nivel === 'alta' ? 'text-[#f2d6c9]' : 'text-medio'}`}>{a.texto}</span>
                    </button>
                  ))}

                  {lote && (
                    <div className="flex flex-none flex-col gap-2 rounded-[18px] border border-borde bg-tarjeta px-4 py-3.5">
                      <div className="flex items-center justify-between gap-3">
                        <h2 className="font-sora text-[15px] font-semibold">Evolución de la roya · {lote.nombre}</h2>
                        <Link to={`/camara?tipo=roya&lote=${lote.id}`} className="flex-none text-sm font-semibold text-ambar hover:text-[#ffd27a]">
                          Escanear
                        </Link>
                      </div>
                      <Evolucion lote={lote} />
                      {lote.muestra.hojas > 0 && (
                        <p className="border-t border-borde pt-2 text-xs leading-relaxed text-medio">
                          Últimos 30 días: <b className="text-texto">{lote.muestra.con_roya} de {lote.muestra.hojas} hojas con roya</b> ({lote.muestra.incidencia}%) y severidad media de {num(lote.muestra.severidad)}%.
                          Orientativo: el monitoreo de Cenicafé evalúa 50 árboles por lote.
                        </p>
                      )}
                    </div>
                  )}

                  <div className="flex flex-none flex-col rounded-[18px] border border-borde bg-tarjeta px-4 py-2">
                    <h2 className="py-1.5 font-sora text-[15px] font-semibold">Últimos escaneos</h2>
                    {datos.recientes.length === 0 && <p className="pb-2 text-sm text-medio">Todavía no hay escaneos.</p>}
                    {datos.recientes.slice(0, 3).map((e) => {
                      const contenido = (
                        <>
                          <span className="text-claro">{e.tipo === 'roya' ? 'Hoja' : 'Racimo'} · Lote {e.lote}{e.foto_ejemplo && ' · foto de ejemplo'}</span>
                          <span className="font-mono text-xs text-medio">{etiquetaEscaneo(e)}</span>
                        </>
                      )
                      const clase = 'flex min-h-10 items-center justify-between gap-3 border-t border-borde py-2 text-sm'
                      return e.ejemplo ? (
                        <div key={e.id} className={clase}>{contenido}</div>
                      ) : (
                        <Link key={e.id} to={`/${e.tipo}/${e.id}`} className={`${clase} hover:text-white`}>{contenido}</Link>
                      )
                    })}
                    {!datos.es_ejemplo && datos.recientes.length > 0 && (
                      <button
                        onClick={async () => {
                          if (!window.confirm('¿Borrar todos sus escaneos, fotos y conversaciones? No se puede deshacer.')) return
                          try {
                            await borrarMisDatos()
                            setElegido(null)
                            cargar()
                          } catch (e) {
                            setError(e.message)
                          }
                        }}
                        className="min-h-10 self-start py-2 text-xs font-semibold text-medio underline underline-offset-4 hover:text-white"
                      >
                        Borrar mis datos
                      </button>
                    )}
                  </div>
                </section>
              </div>
            </>
          )}
        </main>
        <NavInferior />
      </div>
    </div>
  )
}
