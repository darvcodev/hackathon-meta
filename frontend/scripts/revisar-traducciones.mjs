// Revisa que cada texto pasado a t('...') tenga su traducción al inglés con las mismas llaves {nombre}.
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const raiz = new URL('../src/', import.meta.url).pathname
const en = JSON.parse(readFileSync(join(raiz, 'en.json'), 'utf8'))

function archivos(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? archivos(join(carpeta, e.name)) : /\.jsx?$/.test(e.name) ? [join(carpeta, e.name)] : [],
  )
}

const usados = new Map()
for (const archivo of archivos(raiz)) {
  const codigo = readFileSync(archivo, 'utf8')
  for (const [, texto] of codigo.matchAll(/\bt\(\s*'((?:[^'\\]|\\.)*)'/g)) usados.set(texto.replace(/\\'/g, "'"), archivo)
}
const listar = process.argv.includes('--listar')

const llaves = (s) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(',')
const errores = []
for (const [texto, archivo] of usados) {
  if (!Object.hasOwn(en, texto)) errores.push(`Falta en en.json: ${JSON.stringify(texto)} (${archivo.replace(raiz, '')})`)
}
for (const [es, ingles] of Object.entries(en)) {
  if (llaves(es) !== llaves(ingles)) errores.push(`Las llaves no coinciden: ${JSON.stringify(es)}`)
}
if (listar) for (const texto of usados.keys()) console.log(texto)
if (errores.length) {
  console.error(errores.join('\n'))
  process.exit(1)
}
console.log(`Traducciones completas: ${usados.size} textos de la interfaz, ${Object.keys(en).length} en en.json.`)
