import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { borrarConversacion, listarConversaciones, obtenerConversacion, obtenerResumen, preguntar } from '../api.js'
import { Error, Icono, InsigniaDemo, NavInferior, NavLateral, fechaCorta, useModo } from '../components/ui.jsx'

const CLAVE = 'royalens-conversacion'
const MAX_PREGUNTA = 1000
const MENSAJES_ENVIADOS = 20
const GENERALES = ['¿Cómo reconozco la roya en una hoja?', '¿Qué diferencia hay entre incidencia y severidad?', '¿Cómo tomo una buena foto para el escáner?']
const BASE = [
  ['Cenicafé, Avances Técnicos 498', 'https://biblioteca.cenicafe.org/bitstream/10778/4244/1/avt0498.pdf'],
  ['Boletín fitosanitario 18', 'https://publicaciones.cenicafe.org/index.php/fitosanitario/article/download/4996/5598/4313'],
]

function leerAbierta() {
  try {
    return sessionStorage.getItem(CLAVE)
  } catch {
    return null
  }
}

function guardarAbierta(id) {
  try {
    if (id) sessionStorage.setItem(CLAVE, id)
    else sessionStorage.removeItem(CLAVE)
  } catch {
    // Sin almacenamiento, al volver se empieza una conversación nueva; el historial sigue en el servidor.
  }
}

function Historial({ conversaciones, abierta, deshabilitado, alAbrir, alBorrar }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2">
      {conversaciones.length === 0 && <p className="px-1 text-sm leading-relaxed text-medio">Sus conversaciones aparecerán aquí.</p>}
      <ul className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
        {conversaciones.map((c) => (
          <li key={c.id} className={`group flex items-stretch rounded-xl ${c.id === abierta ? 'bg-activo' : 'hover:bg-[#12291d]'}`}>
            <button
              disabled={deshabilitado}
              aria-current={c.id === abierta ? 'true' : undefined}
              onClick={() => alAbrir(c.id)}
              className="flex min-h-12 min-w-0 flex-1 flex-col justify-center gap-0.5 px-3 py-2 text-left disabled:opacity-60"
            >
              <span className="truncate text-sm font-medium text-texto">{c.titulo}</span>
              <span className="font-mono text-[11px] text-suave">{fechaCorta(c.actualizado)} · {c.preguntas} {c.preguntas === 1 ? 'pregunta' : 'preguntas'}</span>
            </button>
            <button
              disabled={deshabilitado}
              aria-label={`Borrar conversación: ${c.titulo}`}
              onClick={() => alBorrar(c)}
              className="flex w-10 flex-none items-center justify-center rounded-r-xl text-suave hover:text-[#ffb4a8] disabled:opacity-60"
            >
              <Icono nombre="basura" tam={16} />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
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
  const [mensajes, setMensajes] = useState([])
  const [conversacionId, setConversacionId] = useState(null)
  const [conversaciones, setConversaciones] = useState([])
  const [verHistorial, setVerHistorial] = useState(false)
  const [borrador, setBorrador] = useState('')
  const [parcial, setParcial] = useState(null)
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(null)
  const [resumen, setResumen] = useState(null)
  const fin = useRef(null)
  const cancelar = useRef(null)
  const botonHistorial = useRef(null)
  const panelHistorial = useRef(null)
  const respondiendo = parcial !== null

  function cerrarHistorial() {
    setVerHistorial(false)
    botonHistorial.current?.focus()
  }

  const refrescar = () => listarConversaciones().then(setConversaciones).catch(() => setConversaciones([]))

  async function abrir(id) {
    setError(null)
    setVerHistorial(false)
    try {
      const c = await obtenerConversacion(id)
      setMensajes(c.mensajes)
      setConversacionId(c.id)
      guardarAbierta(c.id)
    } catch {
      nueva()
    }
  }

  function nueva() {
    setMensajes([])
    setConversacionId(null)
    setError(null)
    setBorrador('')
    setVerHistorial(false)
    guardarAbierta(null)
  }

  async function borrar(c) {
    if (!window.confirm(`¿Borrar la conversación "${c.titulo}"?`)) return
    try {
      await borrarConversacion(c.id)
      if (c.id === conversacionId) nueva()
      refrescar()
    } catch (e) {
      setError({ mensaje: e.message })
    }
  }

  useEffect(() => {
    obtenerResumen().then(setResumen).catch(() => setResumen(null))
    refrescar()
    // Una pregunta sobre un escaneo empieza limpia; si no, se retoma lo que estaba abierto.
    const pedida = parametros.get('conversacion') ?? (escaneoId ? null : leerAbierta())
    if (pedida) abrir(pedida)
    else guardarAbierta(null)
    return () => cancelar.current?.abort()
  }, [])

  useEffect(() => {
    fin.current?.scrollIntoView({ block: 'end' })
  }, [mensajes, parcial, estado, error])

  useEffect(() => {
    if (!verHistorial) return undefined
    const cerrarConEscape = (e) => {
      if (e.key === 'Escape') {
        cerrarHistorial()
      } else if (e.key === 'Tab') {
        const controles = [...panelHistorial.current.querySelectorAll('button:not(:disabled)')]
        const primero = controles[0]
        const ultimo = controles.at(-1)
        if (e.shiftKey && document.activeElement === primero) {
          e.preventDefault()
          ultimo.focus()
        } else if (!e.shiftKey && document.activeElement === ultimo) {
          e.preventDefault()
          primero.focus()
        }
      }
    }
    document.addEventListener('keydown', cerrarConEscape)
    return () => document.removeEventListener('keydown', cerrarConEscape)
  }, [verHistorial])

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
    let idActual = conversacionId
    try {
      await preguntar(
        { mensajes: historial.slice(-MENSAJES_ENVIADOS).map(({ rol, texto }) => ({ rol, texto })), conversacionId: idActual, escaneoId, lote },
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
          } else if (e.tipo === 'conversacion') {
            idActual = e.id
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
      setConversacionId(idActual)
      guardarAbierta(idActual)
      refrescar()
    }
    setParcial(null)
    setEstado(null)
  }

  return (
    <div className="flex h-dvh overflow-hidden">
      <NavLateral />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-none items-center justify-between gap-3 border-b border-[#1b3428] px-4 py-3 lg:min-h-[76px] lg:px-9">
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <h1 className="font-sora text-xl font-extrabold lg:text-[22px]">Asistente</h1>
            <span className="truncate text-[13px] text-suave">{escaneoId ? 'Pregunta sobre este resultado' : 'Pregunta sobre su cafetal · con Muse Spark'}</span>
          </div>
          <div className="flex flex-none items-center gap-2">
            {modo === 'demo' && <span className="rounded-lg border border-ambar/60 bg-ambar/10 px-2 py-1 font-mono text-[11px] font-semibold text-ambar-claro sm:hidden">DEMO</span>}
            <div className="hidden sm:block"><InsigniaDemo modo={modo} /></div>
            <button
              disabled={respondiendo}
              onClick={nueva}
              title="Nueva conversación"
              className="flex h-11 items-center gap-2 rounded-xl bg-ambar px-3 text-sm font-bold text-[#1a1206] hover:bg-[#ffc85e] disabled:opacity-60 md:px-4"
            >
              <Icono nombre="mas" tam={18} grosor={2.6} />
              <span className="sr-only md:not-sr-only">Nueva conversación</span>
            </button>
            <button
              ref={botonHistorial}
              aria-label="Historial de conversaciones"
              aria-controls="panel-historial"
              aria-expanded={verHistorial}
              onClick={() => setVerHistorial((v) => !v)}
              title="Historial de conversaciones"
              className="flex size-11 items-center justify-center rounded-xl border border-borde-fuerte text-texto hover:border-ambar"
            >
              <Icono nombre="historial" tam={20} />
            </button>
          </div>
        </header>

        {verHistorial && (
          <div className="fixed inset-0 z-50">
            <button aria-label="Cerrar historial" onClick={cerrarHistorial} className="absolute inset-0 bg-black/60" />
            <aside ref={panelHistorial} id="panel-historial" role="dialog" aria-modal="true" aria-labelledby="titulo-historial" className="absolute inset-y-0 right-0 flex w-full max-w-[360px] flex-col gap-5 border-l border-borde-fuerte bg-bosque p-4 shadow-2xl sm:p-6">
              <div className="flex flex-none items-center justify-between gap-3 border-b border-borde pb-4">
                <div>
                  <h2 id="titulo-historial" className="font-sora text-lg font-bold">Historial</h2>
                  <p className="mt-1 text-xs text-suave">Conversaciones de los últimos 30 días</p>
                </div>
                <button aria-label="Cerrar historial" onClick={cerrarHistorial} autoFocus className="flex size-10 items-center justify-center rounded-xl border border-borde-fuerte hover:border-ambar">
                  <Icono nombre="cerrar" tam={18} />
                </button>
              </div>
              <Historial
                conversaciones={conversaciones}
                abierta={conversacionId}
                deshabilitado={respondiendo}
                alAbrir={abrir}
                alBorrar={borrar}
              />
            </aside>
          </div>
        )}
        <main className="flex min-h-0 min-w-0 flex-1 flex-col">
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
