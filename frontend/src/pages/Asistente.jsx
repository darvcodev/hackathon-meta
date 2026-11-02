import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { obtenerResumen, preguntar } from '../api.js'
import { Error, Icono, InsigniaDemo, NavInferior, NavLateral, useModo } from '../components/ui.jsx'

const CLAVE = 'royalens-chat'
const MAX_PREGUNTA = 1000
const GENERALES = ['¿Cómo reconozco la roya en una hoja?', '¿Qué diferencia hay entre incidencia y severidad?', '¿Cómo tomo una buena foto para el escáner?']
const BASE = [
  ['Cenicafé, Avances Técnicos 498', 'https://biblioteca.cenicafe.org/bitstream/10778/4244/1/avt0498.pdf'],
  ['Boletín fitosanitario 18', 'https://publicaciones.cenicafe.org/index.php/fitosanitario/article/download/4996/5598/4313'],
]

function leerGuardados() {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE)) ?? []
  } catch {
    return []
  }
}

function sugerencias(resumen, escaneoId) {
  const propias = []
  if (escaneoId) propias.push('¿Qué significa este resultado y qué debería hacer?')
  const alta = resumen?.alertas.find((a) => a.nivel === 'alta')
  if (alta) propias.push(`¿Qué hago con el Lote ${alta.lote}?`)
  if (resumen?.recientes.length) propias.push('¿Cómo va mi finca?')
  return [...propias, ...GENERALES].slice(0, 4)
}

function Burbuja({ mensaje }) {
  const propio = mensaje.rol === 'usuario'
  return (
    <div className={`flex ${propio ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] flex-col gap-2 rounded-2xl px-4 py-3 text-[15px] leading-relaxed lg:max-w-[70%] ${propio ? 'bg-ambar text-[#1a1206]' : 'border border-borde bg-tarjeta text-claro'}`}>
        <p className="whitespace-pre-wrap">{mensaje.texto.replaceAll('**', '')}</p>
        {mensaje.citas?.length > 0 && (
          <div className="flex flex-col gap-1 border-t border-borde pt-2 text-xs text-medio">
            <span className="font-semibold">{mensaje.tituloCitas}</span>
            {mensaje.citas.map((c) => (
              <a key={c.url} href={c.url} target="_blank" rel="noreferrer" className="truncate underline hover:text-texto">
                {c.titulo}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Asistente() {
  const [parametros] = useSearchParams()
  const escaneoId = parametros.get('escaneo')
  const lote = Number(parametros.get('lote')) || null
  const modo = useModo()
  const [mensajes, setMensajes] = useState(leerGuardados)
  const [borrador, setBorrador] = useState('')
  const [parcial, setParcial] = useState(null)
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(null)
  const [resumen, setResumen] = useState(null)
  const fin = useRef(null)
  const cancelar = useRef(null)
  const respondiendo = parcial !== null

  useEffect(() => {
    obtenerResumen().then(setResumen).catch(() => setResumen(null))
    return () => cancelar.current?.abort()
  }, [])

  useEffect(() => {
    try {
      sessionStorage.setItem(CLAVE, JSON.stringify(mensajes))
    } catch {
      // Sin almacenamiento, la conversación solo dura mientras la página esté abierta.
    }
  }, [mensajes])

  useEffect(() => {
    fin.current?.scrollIntoView({ block: 'end' })
  }, [mensajes, parcial, estado, error])

  async function enviar(texto) {
    const pregunta = texto.trim()
    if (!pregunta || respondiendo) return
    const historial = [...mensajes, { rol: 'usuario', texto: pregunta }]
    setMensajes(historial)
    setBorrador('')
    setError(null)
    setParcial('')
    setEstado(null)

    const control = new AbortController()
    cancelar.current = control
    let acumulado = ''
    let citas = []
    let tituloCitas = null
    let fallo = null
    try {
      await preguntar(
        { mensajes: historial.map(({ rol, texto }) => ({ rol, texto })), escaneoId, lote },
        (e) => {
          if (e.tipo === 'texto') {
            acumulado += e.delta
            setEstado(null)
            setParcial(acumulado)
          } else if (e.tipo === 'reinicio') {
            acumulado = ''
            setParcial('')
          } else if (e.tipo === 'estado') {
            setEstado(e.texto)
          } else if (e.tipo === 'reemplazo') {
            acumulado = e.texto
            setParcial(acumulado)
          } else if (e.tipo === 'citas') {
            citas = e.citas
            tituloCitas = e.titulo
          } else if (e.tipo === 'error') {
            fallo = e.mensaje
          }
        },
        control.signal,
      )
      if (!fallo && !acumulado.trim()) fallo = 'El asistente no devolvió ninguna respuesta.'
    } catch (e) {
      if (e.name === 'AbortError') return
      fallo = e.message
    }
    // Un error nunca deja una respuesta a medias en la conversación.
    if (fallo) {
      setError({ mensaje: fallo, pregunta })
      setMensajes(mensajes)
      setBorrador(pregunta)
    } else {
      setMensajes([...historial, { rol: 'asistente', texto: acumulado, citas, tituloCitas }])
    }
    setParcial(null)
    setEstado(null)
  }

  return (
    <div className="flex h-dvh overflow-hidden">
      <NavLateral />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-none flex-wrap items-center justify-between gap-3 border-b border-[#1b3428] px-4 py-3 lg:min-h-[76px] lg:px-9">
          <div className="flex min-w-0 flex-col gap-0.5">
            <h1 className="font-sora text-xl font-extrabold lg:text-[22px]">Asistente</h1>
            <span className="truncate text-[13px] text-suave">{escaneoId ? 'Pregunta sobre este resultado' : 'Pregunta sobre su cafetal · con Muse Spark'}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <InsigniaDemo modo={modo} />
            {mensajes.length > 0 && (
              <button
                disabled={respondiendo}
                onClick={() => {
                  setMensajes([])
                  setError(null)
                }}
                className="h-11 rounded-xl border border-borde-fuerte px-4 text-sm font-semibold hover:border-ambar disabled:opacity-60"
              >
                Nueva conversación
              </button>
            )}
          </div>
        </header>

        <main className="flex min-h-0 flex-1 flex-col">
          <div role="log" aria-live="polite" aria-label="Conversación" className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-5 lg:px-9">
            {mensajes.length === 0 && !respondiendo && (
              <div className="m-auto flex w-full max-w-[640px] flex-col gap-4 text-center">
                <h2 className="font-sora text-2xl font-extrabold">¿En qué le ayudo hoy?</h2>
                <p className="leading-relaxed text-medio">Conozco los escaneos de su finca y me apoyo en documentos de Cenicafé. Oriento, pero no reemplazo al extensionista.</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {sugerencias(resumen, escaneoId).map((s) => (
                    <button key={s} onClick={() => enviar(s)} className="min-h-14 rounded-xl border border-borde-fuerte bg-tarjeta px-4 py-3 text-left text-sm font-medium hover:border-ambar">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {mensajes.map((m, i) => (
              <Burbuja key={i} mensaje={m} />
            ))}
            {respondiendo && (parcial ? <Burbuja mensaje={{ rol: 'asistente', texto: parcial }} /> : (
              <p role="status" className="rl-respirar text-sm text-medio">{estado ?? 'Pensando…'}</p>
            ))}
            {error && <Error mensaje={error.mensaje} alReintentar={() => enviar(error.pregunta)} />}
            <div ref={fin} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              enviar(borrador)
            }}
            className="flex flex-none flex-col gap-2 border-t border-[#1b3428] px-4 py-3 lg:px-9"
          >
            <div className="flex items-end gap-2">
              <label htmlFor="pregunta" className="sr-only">Su pregunta</label>
              <textarea
                id="pregunta"
                rows={1}
                value={borrador}
                maxLength={MAX_PREGUNTA}
                placeholder="Escriba su pregunta…"
                onChange={(e) => setBorrador(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    enviar(borrador)
                  }
                }}
                className="max-h-32 min-h-12 flex-1 resize-none rounded-xl border border-borde-fuerte bg-tarjeta px-4 py-3 text-[15px] text-texto outline-none placeholder:text-suave focus:border-ambar"
              />
              <button
                type="submit"
                aria-label="Enviar pregunta"
                disabled={respondiendo || !borrador.trim()}
                className="flex size-12 flex-none items-center justify-center rounded-xl bg-ambar text-[#1a1206] hover:bg-[#ffc85e] disabled:opacity-50"
              >
                <Icono nombre="enviar" grosor={2.6} />
              </button>
            </div>
            <p className="text-xs leading-relaxed text-suave">
              Orientación general: el manejo con productos lo define su extensionista. Base de consulta:{' '}
              {BASE.map(([titulo, url], i) => (
                <span key={url}>
                  {i > 0 && ' y '}
                  <a href={url} target="_blank" rel="noreferrer" className="underline hover:text-texto">{titulo}</a>
                </span>
              ))}
              .
            </p>
          </form>
        </main>
        <NavInferior />
      </div>
    </div>
  )
}
