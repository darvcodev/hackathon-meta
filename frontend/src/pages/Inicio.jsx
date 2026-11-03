import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ConstruidoConMeta, Icono, Logo, SelectorIdioma } from '../components/ui.jsx'
import { t } from '../i18n.js'

const DETECCIONES = [
  { estilo: 'left-[3%] top-[66%] border-[#e88a2a] text-[#ffd3a6]', texto: 'ROYA · HOJA' },
  { estilo: 'left-[35%] top-[36%] border-ambar text-ambar-claro', texto: 'MADURO · CEREZA' },
  { estilo: 'right-[2%] top-[66%] border-exito text-[#c8f2d3]', texto: 'VERDE · CEREZA' },
]

const PASOS = [
  { to: '/camara', icono: 'camara', etiqueta: 'USTED', titulo: 'Tome la foto', texto: 'Una hoja o un racimo, con su celular, en el cafetal.' },
  { to: '/roya', icono: 'hoja', etiqueta: 'META · SAM 3.1', titulo: 'SAM encuentra', texto: 'Delimita la hoja, cada lesión de roya y cada cereza.' },
  { to: '/maduracion', icono: 'cerezas', etiqueta: 'ROYALENS', titulo: 'La app mide', texto: 'Calcula el área afectada y cuenta las cerezas desde esas máscaras.' },
  { to: '/asistente', icono: 'chat', etiqueta: 'META · MUSE SPARK', titulo: 'Muse explica', texto: 'Cuenta lo que ve en palabras de finca y responde sus dudas.' },
  { to: '/finca', icono: 'casa', etiqueta: 'MI FINCA', titulo: 'Queda en su lote', texto: 'Historial, alertas e incidencia para revisar cada mañana.' },
]

function Escaner() {
  return (
    <div className="rl-flotar relative aspect-square w-full max-w-[min(480px,50vh)]">
      <svg aria-hidden="true" viewBox="0 0 520 520" className="absolute inset-0 size-full">
        <g className="rl-anillo-a">
          <circle cx="260" cy="260" r="246" fill="none" stroke="#F2B544" strokeOpacity=".35" strokeDasharray="2 10" />
          <path d="M260 14 A246 246 0 0 1 474 138" fill="none" stroke="#F2B544" strokeWidth="3" />
          <path d="M46 382 A246 246 0 0 1 20 300" fill="none" stroke="#F2B544" strokeWidth="3" />
        </g>
        <g className="rl-anillo-b">
          <circle cx="260" cy="260" r="222" fill="none" stroke="#5FCB7E" strokeOpacity=".35" strokeWidth="8" strokeDasharray="40 18" />
        </g>
      </svg>
      <div className="absolute inset-[11%] overflow-hidden rounded-full border border-[#24493a]">
        <img src="/img/rama-escaner.jpg" alt={t('Rama de café con cerezas en distintos grados de maduración y una hoja con roya')} className="size-full object-cover" />
        <div className="rl-linea" />
      </div>
      {DETECCIONES.map((d, i) => (
        <motion.div
          key={d.texto}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 + i * 0.25 }}
          className={`absolute rounded-lg border bg-tarjeta/95 px-2.5 py-1.5 font-mono text-[11px] whitespace-nowrap ${d.estilo}`}
        >
          {t(d.texto)}
        </motion.div>
      ))}
    </div>
  )
}

function Paso({ paso, indice }) {
  const deMeta = paso.etiqueta.startsWith('META')
  return (
    <motion.li initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + indice * 0.12, duration: 0.4 }} className="min-w-0">
      <Link
        to={paso.to}
        className={`flex h-full flex-col gap-1.5 rounded-[18px] border bg-tarjeta/90 px-4 py-3.5 backdrop-blur-sm hover:border-ambar ${deMeta ? 'border-ambar/60' : 'border-[#23463a]'}`}
      >
        <span className="flex items-center justify-between gap-2 font-mono text-[10.5px] tracking-[1px]">
          <span className={deMeta ? 'text-ambar' : 'text-suave'}>{t(paso.etiqueta)}</span>
          <Icono nombre={paso.icono} tam={18} className={deMeta ? 'flex-none text-ambar' : 'flex-none text-medio'} />
        </span>
        <span className="font-sora text-[17px] font-semibold text-white">
          <span className="mr-1.5 text-suave">{indice + 1}.</span>
          {t(paso.titulo)}
        </span>
        <span className="text-[13px] leading-snug text-medio">{t(paso.texto)}</span>
      </Link>
    </motion.li>
  )
}

export default function Inicio() {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-hidden lg:h-dvh">
      <img src="/img/fondo.jpg" alt="" aria-hidden="true" className="absolute inset-0 size-full object-cover object-[70%_60%]" />
      <div className="absolute inset-0 bg-gradient-to-r from-bosque via-bosque/75 to-bosque/10" />
      <div className="absolute inset-0 bg-gradient-to-t from-bosque via-bosque/20 to-bosque/50" />
      <div aria-hidden="true" className="relative z-10 flex h-1 flex-none">
        <span className="w-1/2 bg-[#FCD116]" />
        <span className="w-1/4 bg-[#003893]" />
        <span className="w-1/4 bg-[#CE1126]" />
      </div>

      <header className="relative z-10 flex h-[68px] flex-none items-center justify-between gap-2 px-4 lg:gap-4 lg:px-16">
        <div className="flex min-w-0 items-center gap-2.5 sm:gap-4">
          <Link to="/" className="flex flex-none items-center gap-2 font-sora text-[19px] font-extrabold whitespace-nowrap text-white sm:text-[22px]">
            <Logo tam={30} />
            RoyaLens
          </Link>
          <span className="hidden flex-none items-center gap-2 border-l border-white/25 pl-2.5 text-xs font-medium text-claro sm:flex sm:pl-4" aria-label={t('Impulsado por IA de Meta')}>
            <img src="/img/meta-symbol.svg" alt="" className="h-[14px] w-auto sm:h-[16px]" />
            <span className="hidden whitespace-nowrap min-[1200px]:inline">{t('Impulsado por IA de Meta')}</span>
          </span>
        </div>
        <nav aria-label={t('Principal')} className="hidden items-center gap-6 text-[15px] font-medium whitespace-nowrap text-claro lg:flex xl:gap-8">
          <Link to="/finca" className="hover:text-white">{t('Mi finca')}</Link>
          <Link to="/roya" className="hover:text-white">{t('Roya')}</Link>
          <Link to="/maduracion" className="hover:text-white">{t('Maduración')}</Link>
          <Link to="/asistente" className="hover:text-white">{t('Asistente')}</Link>
          <Link to="/estadisticas" className="hover:text-white">{t('Estadísticas')}</Link>
        </nav>
        <div className="flex flex-none items-center gap-2">
          <SelectorIdioma />
          <Link to="/finca" className="inline-flex h-11 items-center rounded-full border border-borde-fuerte bg-bosque/40 px-3 text-sm font-semibold whitespace-nowrap hover:border-ambar sm:px-5">
            <span className="sm:hidden">{t('Mi finca')}</span><span className="hidden sm:inline">{t('Ver mi finca')}</span>
          </Link>
        </div>
      </header>

      <main className="relative z-10 flex min-h-0 flex-1 flex-col gap-5 px-4 pb-4 lg:px-16">
        <div className="grid min-h-0 flex-1 items-center gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
          <motion.section initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="flex flex-col gap-4 pt-4 lg:pt-0">
            <span className="font-mono text-xs tracking-[1.5px] text-ambar">{t('DEL CAFETAL COLOMBIANO, IMPULSADO POR IA DE META')}</span>
            <h1 className="font-sora text-[44px] leading-[1.04] font-extrabold tracking-tight xl:text-[64px]">
              {t('Su cafetal,')}
              <br />
              <span className="text-ambar">{t('visto por IA.')}</span>
            </h1>
            <p className="max-w-[560px] text-lg leading-relaxed text-claro">
              {t('Con una foto del celular, RoyaLens estima cuánta roya tiene cada hoja y cuántas cerezas de cada racimo están en punto. Luego le explica qué significa, en palabras de finca.')}
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/camara" className="inline-flex h-14 items-center gap-2.5 rounded-[14px] bg-ambar px-7 font-bold text-[#1a1206] hover:bg-[#ffc85e]">
                <Icono nombre="camara" grosor={2.2} />
                {t('Escanear ahora')}
              </Link>
              <Link to="/asistente" className="inline-flex h-14 items-center gap-2.5 rounded-[14px] border border-borde-fuerte bg-bosque/40 px-6 font-semibold hover:border-ambar">
                <Icono nombre="chat" />
                {t('Hacer una pregunta')}
              </Link>
            </div>
            <ConstruidoConMeta className="text-sm text-medio" />
          </motion.section>
          <div className="hidden justify-center md:flex">
            <Escaner />
          </div>
        </div>

        <section aria-labelledby="como-funciona" className="flex flex-none flex-col gap-2.5">
          <h2 id="como-funciona" className="font-sora text-[15px] font-semibold text-claro">{t('Cómo funciona')}</h2>
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {PASOS.map((p, i) => (
              <Paso key={p.titulo} paso={p} indice={i} />
            ))}
          </ol>
        </section>

      </main>
    </div>
  )
}
