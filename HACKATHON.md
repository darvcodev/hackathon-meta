# Guía de entrega · Meta Global AI Developer Hackathon

RoyaLens participa en el track **Indie developer**, bajo el tema **Build for Your World**. La entrega se hace en el [formulario del evento](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) hasta el **4 de noviembre de 2026 a las 9:00 p. m. ET** (9:00 p. m. en Bogotá). El 3 de noviembre es el último día completo para preguntas de entrega.

## Requisitos y evaluación

- El repositorio debe ser público.
- El video dura tres minutos y muestra funciones, código y funcionamiento creados durante el evento. Debe quedar claro qué se construyó en ese periodo.
- Los jueces evalúan el video, el código y el producto en vivo. El formulario no tiene un campo para la URL de la app: debe ir en la descripción, en el README y en el video.
- Solo se pueden usar código, datos y recursos sobre los que se tengan derechos.

| Criterio | Peso |
|---|---|
| Impacto | 30 % |
| Uso de las herramientas de IA de Meta | 25 % |
| Demo | 25 % |
| Profundidad técnica y ejecución | 20 % |

Los cinco mejores proyectos de cada track pasan a la final del 9 de noviembre. Las reglas completas están en la [guía del participante](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details) y en las [reglas oficiales](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver).

## Qué mostrar a los jueces

1. Una foto de una hoja: SAM 3.1 delimita hoja y lesiones; RoyaLens calcula el porcentaje afectado desde las máscaras; Muse Spark interpreta el resultado.
2. Una foto de un racimo: SAM 3.1 encuentra cerezas; RoyaLens cuenta y clasifica por color; Muse Spark confirma el contexto y explica el conteo.
3. Mi finca: un escaneo queda en el lote del visitante, con historial e indicadores. Antes del primer escaneo aparece una finca de ejemplo, rotulada como tal.
4. Asistente: responde con el contexto de los escaneos, muestra fuentes cuando consulta la web y guarda un historial de conversaciones.
5. Estadísticas: incidencia, severidad, evolución por lote, cerezas por estado y últimas preguntas, calculadas desde los datos del visitante.

La app contiene ocho imágenes de ejemplo para que los jueces puedan probar los flujos sin estar en un cafetal: dos fotos libres de derechos y seis imágenes generadas con IA, rotuladas como tales. Se procesan una sola vez y después se reutiliza el resultado guardado. Sus resultados aparecen marcados como ejemplo en Mi finca y Estadísticas.

## Evidencia y límites

| Flujo | Evaluación realizada | Límite que debe comunicarse |
|---|---|---|
| Roya | Se probaron hojas con roya, sanas, con otras manchas, fotos malas y escenas que no son hojas. | Los umbrales se ajustaron con la misma muestra; no hay mediciones de referencia hechas por un agrónomo. Variaciones de luz movieron una medición hasta unos 10 puntos. |
| Maduración | Se compararon 6 conteos de la app con conteos visuales sobre las fotos y se probaron escenas que debían rechazarse. | Las cerezas ocultas no se cuentan. Sombra y variedades amarillas pueden alterar la clasificación. Falta evaluación de campo. |
| Asistente | Se revisaron 21 preguntas de prueba, incluidos datos del lote y preguntas sobre productos. | Muse puede variar entre corridas. El filtro de dosis no cubre todas las formas de expresarlas y la respuesta no ha tenido revisión agronómica. |

Las cifras provienen de las evaluaciones locales del proyecto; se pueden repetir con fotos propias mediante `scripts/evaluar_roya.py`, `scripts/evaluar_maduracion.py` y `scripts/evaluar_chat.py`. Estos comandos usan la API y consumen créditos. Las fotos de calibración de terceros no forman parte del repositorio; se conservan fuera de Git con sus fuentes y licencias.

## Cambiar una foto de ejemplo

1. Reemplazar el archivo en `frontend/public/img/ejemplos/`, con el mismo nombre y en formato JPG.
2. Actualizar `credito` y `url` del ejemplo en `backend/ejemplos.py`. Una foto propia usa `"generada": False`, `"credito": "Foto propia"` y `"url": None`.
3. Subir `VERSION_ANALISIS` en ese archivo para que no se reutilice el resultado de la foto anterior.
4. Abrir el ejemplo en la app y revisar que el resultado corresponda a la foto nueva.

Las ocho imágenes actuales son de dominio público, CC0 o generadas con IA. Las fotos reales propias se pueden agregar con estos mismos pasos.

## Despliegue en Coolify

1. Crear una aplicación desde este repositorio y seleccionar el `Dockerfile` de la raíz. El contenedor sirve frontend y API en el puerto **8000**.
2. Configurar un dominio con HTTPS. La cámara en vivo del celular requiere un contexto seguro.
3. Definir las variables de entorno de la tabla siguiente y montar almacenamiento persistente en `/data`. La imagen inicia en modo real.
4. Asignar al menos **1 GB de memoria** como punto de partida. El servidor limita los análisis simultáneos; observar el consumo real después de publicar.
5. Comprobar el health check de `/api/estado`, las cookies y los límites por IP detrás del proxy.

| Variable | ¿Obligatoria? | Valor | Uso |
|---|---|---|---|
| `MODEL_API_KEY` | Sí, como secreto | La clave de dev.meta.ai | Llamadas a SAM 3.1 y Muse Spark |
| `ROYALENS_MODE` | No | `real` | Ya viene en la imagen; `demo` no usa la API |
| `ROYALENS_DATA` | No | `/data` | Ya viene en la imagen; debe coincidir con el volumen |
| `ROYALENS_LIMITE_ANALISIS_IP` | No | `40` | Análisis por IP al día |
| `ROYALENS_LIMITE_ANALISIS` | No | `800` | Análisis en total al día |
| `ROYALENS_LIMITE_CHAT_IP` | No | `60` | Preguntas por IP al día |
| `ROYALENS_LIMITE_CHAT` | No | `1500` | Preguntas en total al día |

Los valores de la tercera columna son los que usa la app si la variable no existe. `ROYALENS_MUSE_MODEL`, `ROYALENS_SAM_MODEL`, `ROYALENS_MIN_CONFIDENCE` y `META_BASE_URL` existen para pruebas y no hace falta definirlas.

## Revisión antes de enviar

- [ ] Abrir la app y la cámara en un celular por HTTPS; analizar una foto real de hoja y otra de racimo.
- [ ] Abrir los ocho ejemplos en inglés y en español. Cada idioma guarda su propio resultado, así que la primera vista de cada uno tarda unos 30 segundos.
- [ ] Cambiar de idioma con las banderas y confirmar que la interfaz, la explicación de Muse y el asistente responden en ese idioma.
- [ ] Comprobar en una ventana privada que el historial y las fotos de otro visitante no son accesibles.
- [ ] Verificar que el asistente responde en streaming y que los enlaces de fuentes funcionan.
- [ ] Redesplegar una vez y confirmar que el volumen de `/data` conserva el historial.
- [ ] Compartir el enlace en una app de mensajería y revisar título, descripción e imagen de vista previa.
- [ ] Revisar en Billing el saldo y la vigencia de los créditos, y mantener la demo activa durante el juicio y la final.
- [ ] Reemplazar en el README «pendiente de publicar» por los enlaces de la demo y del video.
- [ ] Grabar el video con datos observados en la app; describir las mediciones como estimaciones.
- [ ] Hacer público el repositorio y abrir en una ventana privada los enlaces del repositorio, el video y la demo.
- [ ] Incluir la URL de la app en la descripción del formulario y enviar.

Fuentes del evento: [Meta Developer](https://dev.meta.ai/events/global-hackathon) y [Cerebral Valley](https://cerebralvalley.ai/e/meta-ai-developer-hackathon).
