import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Icono, Logo } from '../components/ui.jsx'

const DETECCIONES = [
  { estilo: 'left-[3%] top-[66%] border-[#e88a2a] text-[#ffd3a6]', texto: 'ROYA · HOJA' },
  { estilo: 'left-[35%] top-[36%] border-ambar text-ambar-claro', texto: 'MADURO · CEREZA' },
  { estilo: 'right-[2%] top-[66%] border-exito text-[#c8f2d3]', texto: 'VERDE · CEREZA' },
]

function Escaner() {
  return (
    <div className="rl-flotar relative aspect-square w-full max-w-[min(520px,58vh)]">
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
        <img src="/img/rama-escaner.jpg" alt="Rama de café con cerezas en distintos grados de maduración y una hoja con roya" className="size-full object-cover" />
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
          {d.texto}
        </motion.div>
      ))}
    </div>
  )
}

function Modulo({ to, icono, color, titulo, texto, pronto }) {
  const contenido = (
    <>
      <div className="flex size-14 flex-none items-center justify-center rounded-[14px]" style={{ background: `${color}22`, color }}>
        <Icono nombre={icono} tam={30} />
      </div>
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2 font-sora text-lg font-semibold">
          {titulo}
          {pronto && <span className="rounded-md bg-[#2b2716] px-2 py-0.5 font-mono text-[11px] text-[#e9d9a8]">PRÓXIMAMENTE</span>}
        </div>
        <div className="text-sm text-medio">{texto}</div>
      </div>
    </>
  )
  const clase = 'flex items-center gap-4 rounded-[18px] border bg-tarjeta/90 px-5 py-4 backdrop-blur-sm'
  if (pronto) return <div className={`${clase} border-dashed border-[#2f5242]`}>{contenido}</div>
  return (
    <Link to={to} className={`${clase} border-[#23463a] hover:border-ambar`}>
      {contenido}
    </Link>
  )
}

export default function Inicio() {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-hidden lg:h-dvh">
      <img src="/img/fondo.jpg" alt="" aria-hidden="true" className="absolute inset-0 size-full object-cover object-[70%_60%]" />
      <div className="absolute inset-0 bg-gradient-to-r from-bosque via-bosque/75 to-bosque/10" />
      <div className="absolute inset-0 bg-gradient-to-t from-bosque via-transparent to-bosque/50" />

      <header className="relative z-10 flex h-[76px] flex-none items-center justify-between gap-4 px-4 lg:px-16">
        <Link to="/" className="flex items-center gap-3 font-sora text-[22px] font-extrabold text-white">
          <Logo />
          RoyaLens
        </Link>
        <nav aria-label="Principal" className="hidden gap-10 text-[15px] font-medium text-claro md:flex">
          <Link to="/finca" className="hover:text-white">Mi finca</Link>
          <Link to="/roya" className="hover:text-white">Roya</Link>
          <Link to="/maduracion" className="hover:text-white">Maduración</Link>
        </nav>
        <Link to="/finca" className="inline-flex h-11 items-center rounded-full border border-borde-fuerte bg-bosque/40 px-5 text-sm font-semibold hover:border-ambar">
          Ver mi finca
        </Link>
      </header>

      <main className="relative z-10 flex min-h-0 flex-1 flex-col justify-between gap-8 px-4 pb-8 lg:px-16 lg:pb-10">
        <div className="grid min-h-0 flex-1 items-center gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col gap-5 pt-6 lg:pt-0"
          >
            <div className="inline-flex items-center gap-2.5 self-start rounded-full border border-[#2c4f3b] bg-bosque/50 px-3.5 py-2 font-mono text-[11px] tracking-[1.5px] text-ambar">
              <span className="size-2 rounded-full bg-exito" />
              SAM 3.1 · MUSE SPARK · META AI
            </div>
            <h1 className="font-sora text-5xl leading-[1.02] font-extrabold tracking-tight xl:text-7xl">
              Tu cafetal,
              <br />
              <span className="text-ambar">visto por IA.</span>
            </h1>
            <p className="max-w-[540px] text-lg leading-relaxed text-claro">
              Toma una foto con el celular. RoyaLens mide la roya en cada hoja y la maduración de cada racimo, y te dice qué hacer, en palabras de finca.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/camara" className="inline-flex h-14 items-center gap-2.5 rounded-[14px] bg-ambar px-7 font-bold text-[#1a1206] hover:bg-[#ffc85e]">
                <Icono nombre="camara" grosor={2.2} />
                Escanear una hoja
              </Link>
              <Link to="/finca" className="inline-flex h-14 items-center rounded-[14px] border border-borde-fuerte bg-bosque/40 px-6 font-semibold hover:border-ambar">
                Ver mi finca
              </Link>
            </div>
          </motion.section>
          <div className="flex justify-center">
            <Escaner />
          </div>
        </div>

        <section aria-label="Módulos" className="grid flex-none gap-4 md:grid-cols-3">
          <Modulo to="/roya" icono="hoja" color="#E88A2A" titulo="Roya en hojas" texto="% de hoja afectada y nivel de severidad" />
          <Modulo to="/maduracion" icono="cerezas" color="#E5483B" titulo="Maduración del grano" texto="Cerezas verdes, pintonas y maduras por racimo" />
          <Modulo pronto icono="suelo" color="#C9B27A" titulo="Salud del suelo" texto="Con análisis de laboratorio y sensores" />
        </section>
      </main>
    </div>
  )
}
