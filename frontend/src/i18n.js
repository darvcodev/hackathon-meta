import { useEffect, useState } from 'react'
import EN from './en.json'

/** La app abre en inglés; el español queda a un toque. Los textos fuente están en español. */
export const IDIOMAS = ['en', 'es']
const CLAVE = 'royalens-idioma'

function inicial() {
  try {
    const guardado = localStorage.getItem(CLAVE)
    if (IDIOMAS.includes(guardado)) return guardado
  } catch {
    // Sin almacenamiento se usa el idioma predeterminado.
  }
  return 'en'
}

let actual = inicial()
const oyentes = new Set()

function aplicar() {
  document.documentElement.lang = actual
  document.title = actual === 'en' ? 'RoyaLens — Powered by Meta AI' : 'RoyaLens — Impulsado por IA de Meta'
  // El servidor lee esta cookie para que Muse responda en el mismo idioma.
  document.cookie = `royalens_idioma=${actual}; path=/; max-age=31536000; samesite=lax`
}
aplicar()

export const idioma = () => actual
export const locale = () => (actual === 'en' ? 'en-US' : 'es-CO')

export function cambiarIdioma(nuevo) {
  if (!IDIOMAS.includes(nuevo) || nuevo === actual) return
  actual = nuevo
  try {
    localStorage.setItem(CLAVE, nuevo)
  } catch {
    // El cambio vale para esta visita aunque no se pueda recordar.
  }
  aplicar()
  oyentes.forEach((avisar) => avisar(nuevo))
}

export function useIdioma() {
  const [valor, setValor] = useState(actual)
  useEffect(() => {
    oyentes.add(setValor)
    return () => oyentes.delete(setValor)
  }, [])
  return valor
}

const decimal = (n) => n.replace(',', '.')

// Mensajes del servidor que llevan cifras o números de lote.
const PATRONES = [
  [/^Lote (\d+)$/, (n) => `Plot ${n}`],
  [/^Lote (\d+) necesita atención$/, (n) => `Plot ${n} needs attention`],
  [/^Revise el Lote (\d+)$/, (n) => `Check Plot ${n}`],
  [/^Lote (\d+): foto de ejemplo$/, (n) => `Plot ${n}: sample photo`],
  [/^Último escaneo hace (\d+) días\.$/, (n) => `Last scan ${n} days ago.`],
  [/^El lote (\d+) no existe\.$/, (n) => `Plot ${n} does not exist.`],
  [/^La pregunta debe tener máximo (\d+) caracteres\.$/, (n) => `The question must be ${n} characters or fewer.`],
  [
    /^La última hoja es una foto de ejemplo, no de su cafetal, y marca ([\d,.]+)% de roya\.$/,
    (p) => `The latest leaf is a sample photo, not from your farm, and shows ${decimal(p)}% rust.`,
  ],
  [
    /^La roya pasó de ([\d,.]+)% a ([\d,.]+)% en las últimas semanas\. Consulte a su extensionista del Comité de Cafeteros\.$/,
    (a, b) => `Rust went from ${decimal(a)}% to ${decimal(b)}% in recent weeks. Talk to your extension agent at the Coffee Growers Committee.`,
  ],
  [
    /^La última hoja escaneada tiene ([\d,.]+)% de roya\. Consulte a su extensionista del Comité de Cafeteros\.$/,
    (p) => `The latest scanned leaf has ${decimal(p)}% rust. Talk to your extension agent at the Coffee Growers Committee.`,
  ],
]

const faltantes = new Set()

function traducir(texto) {
  if (actual === 'es' || typeof texto !== 'string') return texto
  if (Object.hasOwn(EN, texto)) return EN[texto]
  for (const [patron, armar] of PATRONES) {
    const partes = texto.match(patron)
    if (partes) return armar(...partes.slice(1))
  }
  if (import.meta.env.DEV && texto && !faltantes.has(texto)) {
    faltantes.add(texto)
    console.warn('Falta traducción:', texto)
  }
  return texto
}

/** Traduce un texto en español. Las llaves {nombre} se llenan con `datos`. */
export function t(texto, datos) {
  const resultado = traducir(texto)
  if (!datos || typeof resultado !== 'string') return resultado
  return resultado.replace(/\{(\w+)\}/g, (_, clave) => String(datos[clave] ?? ''))
}
