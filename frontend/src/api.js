async function pedir(url, opciones) {
  let respuesta
  try {
    respuesta = await fetch(url, opciones)
  } catch {
    throw new Error('No hay conexión con el servidor.')
  }
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    throw new Error(datos?.detail || `El servidor respondió con error ${respuesta.status}.`)
  }
  return datos
}

export const obtenerEstado = () => pedir('/api/estado')
export const obtenerResumen = () => pedir('/api/resumen')
export const obtenerEscaneo = (id) => pedir(`/api/escaneos/${id}`)

export function analizar(tipo, foto, lote) {
  const cuerpo = new FormData()
  cuerpo.append('foto', foto, foto.name || 'foto.jpg')
  cuerpo.append('lote', String(lote))
  return pedir(`/api/${tipo}`, { method: 'POST', body: cuerpo })
}

export async function fotoDeEjemplo(ruta) {
  const respuesta = await fetch(ruta)
  if (!respuesta.ok) throw new Error('No se pudo cargar la foto de ejemplo.')
  return new File([await respuesta.blob()], ruta.split('/').pop(), { type: 'image/jpeg' })
}
