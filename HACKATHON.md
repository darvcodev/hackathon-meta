# Guía de entrega · Meta Global AI Developer Hackathon

RoyaLens participa en el track **Indie developer**, bajo el tema **Build for Your World**. La evaluación anunciada para este track considera creatividad, ambición técnica y funcionamiento. Las [fechas y criterios públicos](https://dev.meta.ai/events/global-hackathon) indican entrega el **4 de noviembre de 2026 a las 9:00 p. m. ET** (9:00 p. m. en Bogotá). Las reglas del formulario para participantes deben revisarse en la cuenta del evento antes de enviar.

## Qué mostrar a los jueces

1. Una foto de una hoja: SAM 3.1 delimita hoja y lesiones; RoyaLens calcula el porcentaje afectado desde las máscaras; Muse Spark interpreta el resultado.
2. Una foto de un racimo: SAM 3.1 encuentra cerezas; RoyaLens cuenta y clasifica por color; Muse Spark confirma el contexto y explica el conteo.
3. Mi finca: un escaneo queda en el lote del visitante, con historial e indicadores. Antes del primer escaneo aparece una finca de ejemplo, rotulada como tal.
4. Asistente: responde con el contexto de los escaneos, muestra fuentes cuando consulta la web y guarda un historial de conversaciones.
5. Estadísticas: incidencia, severidad, evolución por lote, cerezas por estado y últimas preguntas, calculadas desde los datos del visitante.

La app contiene ocho fotos de ejemplo para que los jueces puedan probar los flujos sin estar en un cafetal. Las fotos de ejemplo se procesan una sola vez y después se reutiliza el resultado guardado.

## Evidencia y límites

| Flujo | Evaluación realizada | Límite que debe comunicarse |
|---|---|---|
| Roya | Se probaron hojas con roya, sanas, con otras manchas, fotos malas y escenas que no son hojas. | Los umbrales se ajustaron con la misma muestra; no hay mediciones de referencia hechas por un agrónomo. Variaciones de luz movieron una medición hasta unos 10 puntos. |
| Maduración | Se compararon 6 conteos de la app con conteos visuales sobre las fotos y se probaron escenas que debían rechazarse. | Las cerezas ocultas no se cuentan. Sombra y variedades amarillas pueden alterar la clasificación. Falta evaluación de campo. |
| Asistente | Se revisaron 21 preguntas de prueba, incluidos datos del lote y preguntas sobre productos. | Muse puede variar entre corridas. El filtro de dosis no cubre todas las formas de expresarlas y la respuesta no ha tenido revisión agronómica. |

Las cifras provienen de las evaluaciones locales del proyecto; se pueden repetir con fotos propias mediante `scripts/evaluar_roya.py`, `scripts/evaluar_maduracion.py` y `scripts/evaluar_chat.py`. Estos comandos usan la API y consumen créditos. Las fotos de calibración de terceros no forman parte del repositorio; se conservan fuera de Git con sus fuentes y licencias.

## Despliegue en Coolify

1. Crear una aplicación desde este repositorio y seleccionar el `Dockerfile` de la raíz. El contenedor sirve frontend y API en el puerto **8000**.
2. Configurar un dominio con HTTPS. La cámara en vivo del celular requiere un contexto seguro.
3. Definir `MODEL_API_KEY` como secreto de ejecución y montar almacenamiento persistente en `/data`. La imagen inicia en modo real.
4. Asignar al menos **1 GB de memoria** como punto de partida. El servidor limita los análisis simultáneos; observar el consumo real después de publicar.
5. Comprobar el health check de `/api/estado`, las cookies y los límites por IP detrás del proxy. Los cupos se ajustan con `ROYALENS_LIMITE_ANALISIS_IP`, `ROYALENS_LIMITE_ANALISIS`, `ROYALENS_LIMITE_CHAT_IP` y `ROYALENS_LIMITE_CHAT`.

## Revisión antes de enviar

- [ ] Abrir la app y la cámara en un celular por HTTPS; analizar una foto real de hoja y otra de racimo.
- [ ] Abrir los ocho ejemplos. Confirmar que cada uno devuelve resultado y que el crédito de la foto aparece en la interfaz.
- [ ] Comprobar en una ventana privada que el historial y las fotos de otro visitante no son accesibles.
- [ ] Verificar que el asistente responde en streaming y que los enlaces de fuentes funcionan.
- [ ] Redesplegar una vez y confirmar que el volumen de `/data` conserva el historial.
- [ ] Compartir el enlace en una app de mensajería y revisar título, descripción e imagen de vista previa.
- [ ] Revisar en el formulario oficial los campos, el video, el acceso al repositorio y el plazo de disponibilidad de la demo.
- [ ] Grabar el video con datos observados en la app; describir las mediciones como estimaciones.

Fuentes del evento: [Meta Developer](https://dev.meta.ai/events/global-hackathon) y [Cerebral Valley](https://cerebralvalley.ai/e/meta-ai-developer-hackathon).
