import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { obtenerEstadisticas } from '../api.js'
import { Error, Icono, InsigniaDemo, NavInferior, NavLateral, fechaCorta, num } from '../components/ui.jsx'
import { colorNivel } from './Roya.jsx'

const COLOR_LOTE = { 1: '#3987E5', 2: '#D95926', 3: '#199E70', 4: '#C98500' }
const NIVELES = ['Sin roya visible', 'Leve', 'Moderada', 'Alta', 'Severa']
const ESTADOS = [
  ['verde', 'Verde', '#7FB04A'],
  ['pinton', 'Pintón', '#E9B23B'],
  ['maduro', 'Maduro', '#E5483B'],
  ['sobremaduro', 'Sobremaduro', '#A23A5E'],
]

const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`

function Tarjeta({ titulo, detalle, children, className = '' }) {
  return (
    <section className={`flex min-w-0 flex-col gap-3 rounded-[18px] border border-borde bg-tarjeta px-4 py-4 lg:px-5 ${className}`}>
      <div className="flex flex-col gap-0.5">
        <h2 className="font-sora text-[15px] font-semibold text-texto">{titulo}</h2>
        {detalle && <p className="text-xs leading-relaxed text-medio">{detalle}</p>}
      </div>
      {children}
    </section>
  )
}

function Cifra({ titulo, valor, detalle }) {
  return (
    <div className="flex min-w-0 flex-col gap-1 rounded-2xl border border-borde bg-tarjeta px-4 py-3.5 lg:px-5">
      <span className="text-[13px] text-suave">{titulo}</span>
      <span className="font-sora text-[28px] leading-tight font-extrabold text-texto">{valor ?? '—'}</span>
      <span className="text-xs text-medio">{detalle}</span>
    </div>
  )
}

function Tendencias({ lotes }) {
  const [foco, setFoco] = useState(null)
  const series = lotes.filter((l) => l.puntos.length > 0)
  if (series.length === 0) return <p className="py-8 text-center text-sm text-medio">Todavía no hay hojas medidas.</p>

  // En el celular el gráfico se dibuja más angosto para que las etiquetas no se vuelvan diminutas.
  const estrecho = window.matchMedia('(max-width: 639px)').matches
  const A = estrecho ? 340 : 640, H = estrecho ? 220 : 240, IZQ = 40, DER = 64, ARR = 14, ABA = 26
  const tiempos = series.flatMap((l) => l.puntos.map((p) => new Date(p.fecha).getTime()))
  const [t0, t1] = [Math.min(...tiempos), Math.max(...tiempos)]
  const techo = Math.max(10, ...series.flatMap((l) => l.puntos.map((p) => p.porcentaje))) * 1.1
  const x = (t) => (t1 === t0 ? (IZQ + A - DER) / 2 : IZQ + ((t - t0) / (t1 - t0)) * (A - IZQ - DER))
  const y = (v) => H - ABA - (v / techo) * (H - ARR - ABA)
  const marcas = [0, techo / 2, techo].map((v) => Math.round(v))
  const puntos = series.flatMap((l) =>
    l.puntos.map((p) => ({ lote: l, p, cx: x(new Date(p.fecha).getTime()), cy: y(p.porcentaje) })),
  )

  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-medio" aria-label="Leyenda">
        {series.map((l) => (
          <li key={l.id} className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 rounded" style={{ background: COLOR_LOTE[l.id] }} />
            {l.nombre}
          </li>
        ))}
      </ul>
      <div className="relative">
        <svg
          role="img"
          aria-label="Severidad de roya por lote a lo largo del tiempo"
          viewBox={`0 0 ${A} ${H}`}
          className="h-auto w-full"
          onMouseLeave={() => setFoco(null)}
        >
          {marcas.map((m) => (
            <g key={m}>
              <line x1={IZQ} x2={A - DER} y1={y(m)} y2={y(m)} stroke="#1F3A2B" />
              <text x={IZQ - 8} y={y(m) + 4} textAnchor="end" fill="#A3BBAA" fontSize="11">{m}%</text>
            </g>
          ))}
          <text x={IZQ} y={H - 8} fill="#A3BBAA" fontSize="11">{fechaCorta(new Date(t0).toISOString())}</text>
          <text x={A - DER} y={H - 8} textAnchor="end" fill="#A3BBAA" fontSize="11">{fechaCorta(new Date(t1).toISOString())}</text>
          {series.map((l) => {
            const c = l.puntos.map((p) => [x(new Date(p.fecha).getTime()), y(p.porcentaje)])
            const [ux, uy] = c[c.length - 1]
            return (
              <g key={l.id}>
                {c.length > 1 && (
                  <path
                    d={`M${c.map((v) => v.join(' ')).join(' L')}`}
                    fill="none"
                    stroke={COLOR_LOTE[l.id]}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}
                <text x={ux + 8} y={uy + 4} fill="#DCE8DF" fontSize="11">{l.nombre}</text>
              </g>
            )
          })}
          {puntos.map((d, i) => (
            <g key={i} onMouseEnter={() => setFoco(d)} onClick={() => setFoco(d)}>
              <circle cx={d.cx} cy={d.cy} r="12" fill="transparent" />
              <circle cx={d.cx} cy={d.cy} r={foco === d ? 5.5 : 4} fill={COLOR_LOTE[d.lote.id]} stroke="#0E2218" strokeWidth="2" />
            </g>
          ))}
        </svg>
        {foco && (
          <div
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg border border-borde-fuerte bg-bosque px-2.5 py-1.5 text-xs whitespace-nowrap text-texto shadow-lg"
            style={{ left: `${(foco.cx / A) * 100}%`, top: `${(foco.cy / H) * 100 - 3}%` }}
          >
            <b>{foco.lote.nombre}</b> · {num(foco.p.porcentaje)}% · {fechaCorta(foco.p.fecha)}
          </div>
        )}
      </div>
    </div>
  )
}

function BarraApilada({ partes, total, etiqueta }) {
  return (
    <div role="img" aria-label={etiqueta} className="flex h-3.5 gap-0.5 overflow-hidden rounded-full bg-borde">
      {partes.filter((p) => p.valor > 0).map((p) => (
        <motion.div
          key={p.nombre}
          title={`${p.nombre}: ${p.valor}`}
          initial={{ width: 0 }}
          animate={{ width: `${(100 * p.valor) / total}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{ background: p.color }}
        />
      ))}
    </div>
  )
}

function Niveles({ roya }) {
  const partes = NIVELES.map((n) => ({ nombre: n, valor: roya.niveles[n] ?? 0, color: colorNivel(n) }))
  if (roya.hojas === 0) return <p className="py-4 text-center text-sm text-medio">Todavía no hay hojas medidas.</p>
  return (
    <div className="flex flex-col gap-3">
      <BarraApilada partes={partes} total={roya.hojas} etiqueta={partes.map((p) => `${p.nombre}: ${p.valor}`).join(', ')} />
      <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[13px] sm:grid-cols-3">
        {partes.map((p) => (
          <li key={p.nombre} className="flex items-center gap-2 text-claro">
            <span className="size-2.5 flex-none rounded-full" style={{ background: p.color }} />
            <span className="min-w-0 truncate">{p.nombre}</span>
            <b className="ml-auto font-mono text-xs text-texto">{p.valor}</b>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Maduracion({ lotes, conteo }) {
  const total = ESTADOS.reduce((s, [k]) => s + conteo[k], 0)
  if (total === 0) return <p className="py-4 text-center text-sm text-medio">Todavía no hay racimos contados.</p>
  return (
    <div className="flex flex-col gap-3">
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-medio" aria-label="Leyenda">
        {ESTADOS.map(([k, nombre, color]) => (
          <li key={k} className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full" style={{ background: color }} />
            {nombre} <b className="font-mono text-texto">{conteo[k]}</b>
          </li>
        ))}
      </ul>
      {lotes.filter((l) => l.racimos > 0).map((l) => {
        const suma = ESTADOS.reduce((s, [k]) => s + l.conteo[k], 0)
        return (
          <div key={l.id} className="flex items-center gap-3 text-[13px]">
            <span className="w-12 flex-none text-claro">{l.nombre}</span>
            <div className="min-w-0 flex-1">
              <BarraApilada
                partes={ESTADOS.map(([k, nombre, color]) => ({ nombre, valor: l.conteo[k], color }))}
                total={suma}
                etiqueta={`${l.nombre}: ${ESTADOS.map(([k, nombre]) => `${nombre} ${l.conteo[k]}`).join(', ')}`}
              />
            </div>
            <span className="w-16 flex-none text-right font-mono text-xs text-medio">{suma} cer.</span>
          </div>
        )
      })}
    </div>
  )
}

function Actividad({ semanas }) {
  const techo = Math.max(1, ...semanas.map((s) => s.escaneos + s.preguntas))
  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-wrap gap-x-4 text-xs text-medio" aria-label="Leyenda">
        <li className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] bg-[#3987E5]" />Escaneos</li>
        <li className="flex items-center gap-1.5"><span className="size-2.5 rounded-[3px] bg-[#C98500]" />Preguntas</li>
      </ul>
      <ol className="flex h-28 items-end gap-1.5">
        {semanas.map((s) => {
          const texto = `Semana al ${fechaCorta(s.fin)}: ${s.escaneos} escaneos y ${s.preguntas} preguntas`
          return (
            <li key={s.inicio} title={texto} aria-label={texto} className="flex h-full min-w-0 flex-1 flex-col justify-end gap-0.5">
              {s.preguntas > 0 && <div className="w-full rounded-t-[4px] bg-[#C98500]" style={{ height: `${(100 * s.preguntas) / techo}%` }} />}
              {s.escaneos > 0 && <div className={`w-full bg-[#3987E5] ${s.preguntas ? '' : 'rounded-t-[4px]'}`} style={{ height: `${(100 * s.escaneos) / techo}%` }} />}
              {s.escaneos + s.preguntas === 0 && <div className="h-0.5 w-full rounded bg-borde" />}
            </li>
          )
        })}
      </ol>
      <div className="flex justify-between font-mono text-[11px] text-suave">
        <span>{fechaCorta(semanas[0].inicio)}</span>
        <span>Hoy</span>
      </div>
    </div>
  )
}

function TablaLotes({ lotes }) {
  const tendencia = (c) => (c === null ? '—' : `${c > 0 ? '+' : ''}${num(c)} pts`)
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-left text-[13px]">
        <thead className="font-mono text-[11px] text-suave">
          <tr>
            {['Lote', 'Hojas', 'Con roya', 'Incidencia', 'Severidad', 'Última', 'Cambio', '% maduro'].map((c) => (
              <th key={c} scope="col" className="py-2 pr-3 font-medium">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {lotes.map((l) => (
            <tr key={l.id} className="border-t border-borde text-claro">
              <th scope="row" className="py-2.5 pr-3 font-semibold text-texto">
                <span className="mr-2 inline-block size-2 rounded-full" style={{ background: COLOR_LOTE[l.id] }} />
                {l.nombre}
              </th>
              <td className="pr-3">{l.hojas}</td>
              <td className="pr-3">{l.con_roya}</td>
              <td className="pr-3">{l.incidencia === null ? '—' : `${l.incidencia}%`}</td>
              <td className="pr-3">{l.severidad === null ? '—' : `${num(l.severidad)}%`}</td>
              <td className="pr-3">{l.ultima_roya === null ? '—' : `${num(l.ultima_roya)}% · ${l.nivel}`}</td>
              <td className="pr-3">{tendencia(l.cambio)}</td>
              <td>{l.maduro === null ? '—' : `${l.maduro}%`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Estadisticas() {
  const [d, setD] = useState(null)
  const [error, setError] = useState(null)
  const cargar = () => {
    setError(null)
    obtenerEstadisticas().then(setD).catch((e) => setError(e.message))
  }
  useEffect(cargar, [])

  return (
    <div className="flex min-h-dvh lg:h-dvh lg:overflow-hidden">
      <NavLateral />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 lg:px-9 lg:py-6">
          <header className="flex flex-wrap items-end justify-between gap-3">
            <div className="flex flex-col gap-1">
              <span className="font-mono text-xs tracking-[1.5px] text-ambar uppercase">Últimos 30 días</span>
              <h1 className="font-sora text-[28px] font-extrabold lg:text-[34px]">Estadísticas de su finca</h1>
            </div>
            <InsigniaDemo modo={d?.modo} />
          </header>

          {error && <Error mensaje={error} alReintentar={cargar} />}
          {!d && !error && <p role="status" className="text-medio">Calculando…</p>}

          {d && (
            <>
              {d.es_ejemplo && (
                <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3">
                  <span className="flex items-start gap-3 text-sm text-ambar-claro">
                    <Icono nombre="alerta" className="mt-0.5 flex-none" />
                    <span><b>Finca de ejemplo.</b> Estas cifras son ilustrativas. Con su primer escaneo verá solo sus datos.</span>
                  </span>
                  <Link to="/roya" className="text-sm font-bold whitespace-nowrap text-ambar underline underline-offset-4">Hacer mi primer escaneo</Link>
                </div>
              )}

              {d.hay_fotos_ejemplo && (
                <div role="status" className="flex items-start gap-3 rounded-2xl border border-ambar/50 bg-[#2a220e] px-4 py-3 text-sm text-ambar-claro">
                  <Icono nombre="alerta" className="mt-0.5 flex-none" />
                  <span><b>Incluye fotos de ejemplo.</b> Esos resultados muestran cómo funciona la app, no el estado de su cafetal. Puede borrarlos con «Borrar mis datos» en Mi finca.</span>
                </div>
              )}
              <section aria-label="Cifras generales" className="grid flex-none grid-cols-2 gap-3 xl:grid-cols-4">
                <Cifra
                  titulo="Incidencia de roya"
                  valor={d.roya.incidencia === null ? null : `${d.roya.incidencia}%`}
                  detalle={`${d.roya.con_roya} de ${plural(d.roya.hojas, 'hoja', 'hojas')} con roya`}
                />
                <Cifra
                  titulo="Severidad media"
                  valor={d.roya.severidad === null ? null : `${num(d.roya.severidad)}%`}
                  detalle="Área afectada por hoja, sanas incluidas"
                />
                <Cifra
                  titulo="Escaneos"
                  valor={d.totales.escaneos}
                  detalle={`${plural(d.totales.hojas, 'hoja', 'hojas')} · ${plural(d.totales.racimos, 'racimo', 'racimos')} · ${d.totales.sin_medicion} sin medición`}
                />
                <Cifra
                  titulo="Preguntas al asistente"
                  valor={d.totales.preguntas}
                  detalle={`En ${d.totales.conversaciones} ${d.totales.conversaciones === 1 ? 'conversación' : 'conversaciones'}`}
                />
              </section>

              <div className="grid flex-none gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
                <Tarjeta titulo="Evolución de la roya por lote" detalle="Porcentaje de hoja afectada en cada escaneo. Pase el cursor o toque un punto para ver el dato.">
                  <Tendencias lotes={d.por_lote} />
                </Tarjeta>
                <div className="flex min-w-0 flex-col gap-4">
                  <Tarjeta titulo="Hojas por nivel de severidad"><Niveles roya={d.roya} /></Tarjeta>
                  <Tarjeta titulo="Actividad de las últimas 8 semanas"><Actividad semanas={d.semanas} /></Tarjeta>
                </div>
              </div>

              <Tarjeta
                titulo="Comparación por lote"
                detalle="Incidencia: hojas con roya sobre hojas escaneadas. Severidad: promedio del área afectada. El monitoreo de Cenicafé evalúa 50 árboles por lote, así que estas cifras son orientativas."
                className="flex-none"
              >
                <TablaLotes lotes={d.por_lote} />
              </Tarjeta>

              <div className="grid flex-none gap-4 pb-2 xl:grid-cols-2">
                <Tarjeta titulo="Cerezas por estado" detalle={d.totales.cerezas ? `${d.totales.cerezas} cerezas contadas en total.` : null}>
                  <Maduracion lotes={d.por_lote} conteo={d.maduracion.conteo} />
                </Tarjeta>
                <Tarjeta titulo="Lo último que preguntó">
                  {d.preguntas.length === 0 ? (
                    <div className="flex flex-col items-start gap-2 py-2 text-sm text-medio">
                      Todavía no ha hecho preguntas.
                      <Link to="/asistente" className="font-semibold text-ambar underline underline-offset-4">Abrir el asistente</Link>
                    </div>
                  ) : (
                    <ul className="flex flex-col">
                      {d.preguntas.map((p, i) => (
                        <li key={i} className="border-t border-borde first:border-t-0">
                          <Link to={`/asistente?conversacion=${p.conversacion}`} className="flex min-h-11 items-center justify-between gap-3 py-2 text-sm text-claro hover:text-white">
                            <span className="min-w-0 truncate">{p.texto}</span>
                            <span className="flex-none font-mono text-[11px] text-suave">{fechaCorta(p.fecha)}</span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </Tarjeta>
              </div>
            </>
          )}
        </main>
        <NavInferior />
      </div>
    </div>
  )
}
