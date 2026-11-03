import { t } from './i18n.js'

async function pedir(url, opciones) {
  let respuesta
  try {
    respuesta = await fetch(url, opciones)
  } catch {
    throw new Error(t('No hay conexión con el servidor.'))
  }
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    throw new Error(typeof datos?.detail === 'string' ? t(datos.detail) : t('El servidor respondió con error {n}.', { n: respuesta.status }))
  }
  return datos
}

export const obtenerEstado = () => pedir('/api/estado')
export const obtenerResumen = () => pedir('/api/resumen')
export const obtenerEscaneo = (id) => pedir(`/api/escaneos/${id}`)

export const obtenerEstadisticas = () => pedir('/api/estadisticas')
export const listarConversaciones = () => pedir('/api/conversaciones')
export const obtenerConversacion = (id) => pedir(`/api/conversaciones/${id}`)
export const borrarConversacion = (id) => pedir(`/api/conversaciones/${id}`, { method: 'DELETE' })
export const obtenerEjemplos = (tipo) => pedir(`/api/ejemplos/${tipo}`)
export const borrarMisDatos = () => pedir('/api/mis-datos', { method: 'DELETE' })

export function analizarEjemplo(slug, lote) {
  const cuerpo = new FormData()
  cuerpo.append('lote', String(lote))
  return pedir(`/api/ejemplos/${slug}`, { method: 'POST', body: cuerpo })
}

export function analizar(tipo, foto, lote) {
  const cuerpo = new FormData()
  cuerpo.append('foto', foto, foto.name || 'foto.jpg')
  cuerpo.append('lote', String(lote))
  return pedir(`/api/${tipo}`, { method: 'POST', body: cuerpo })
}

/** Envía la conversación y llama a `alEvento` con cada evento de la respuesta. */
export async function preguntar({ mensajes, conversacionId, escaneoId, lote }, alEvento, senal) {
  let respuesta
  try {
    respuesta = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensajes, conversacion_id: conversacionId ?? null, escaneo_id: escaneoId ?? null, lote: lote ?? null }),
      signal: senal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new Error(t('No hay conexión con el servidor.'))
  }
  if (!respuesta.ok) {
    const datos = await respuesta.json().catch(() => null)
    const detalle = typeof datos?.detail === 'string' ? datos.detail : null
    throw new Error(detalle ? t(detalle) : t('El servidor respondió con error {n}.', { n: respuesta.status }))
  }
  const lector = respuesta.body.pipeThrough(new TextDecoderStream()).getReader()
  let resto = ''
  for (;;) {
    const { value, done } = await lector.read()
    if (done) break
    const lineas = (resto + value).split('\n')
    resto = lineas.pop()
    for (const linea of lineas) if (linea.trim()) alEvento(JSON.parse(linea))
  }
}
