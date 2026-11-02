# Plan de RoyaLens hasta la entrega

Entrega: miércoles 4 de noviembre de 2026, 9:00 p. m. (GMT-5). Meta interna: enviar antes del mediodía.

## Decisiones

- **Logo de Meta:** no se usa sin aprobación. La guía de marca de Meta dice que todo uso del logo la requiere.
  En Inicio va en texto: "Construido con SAM 3.1 y Muse Spark de Meta". Si lo aprueban, se agrega en un solo componente.
- **APIs:** solo las de Meta. SAM 3.1 mide, Muse Spark explica y conversa, Muse Image crea imágenes de presentación
  y Muse Voice Transcribe es opcional para preguntar por voz.
- **Mini chat:** se incluye.
- **Escala de severidad:** sigue marcada como orientativa, salvo que la valide un agrónomo.

## Fases

Estado: `[ ]` pendiente, `[~]` parcial, `[x]` terminada.

### [~] Fase 0: Bases (dom 1)
- [x] Plan y libreto en `docs/`.
- [x] Requisitos públicos en `docs/ENTREGA.md`.
- [x] Primer lote de fotos en `fotos/`, con fuentes y licencias.
- [ ] Reglas oficiales de entrega: requieren la sesión de Daniel.
- [ ] Saldo en Billing de dev.meta.ai: requiere la sesión de Daniel.

**Listo cuando:** conozcamos los requisitos exactos y las fotos estén en `fotos/`.

### [~] Fase 1: Roya real de punta a punta (dom 1 y lun 2 por la mañana)
Resultados y límites en `docs/CALIBRACION.md`.

- [~] Probar con al menos 10 hojas con roya, 5 sanas, 5 fotos que no sean hojas y 5 fotos malas. Van 5, 2, 5 y 5.
- [x] Afinar los prompts de lesión y agregar el filtro de color.
- [x] Basar la escala en el diagrama de Cenicafé.
- [x] Mostrar el análisis de Muse completo en la pantalla.
- [ ] Repetir la evaluación con fotos reales de Daniel.

**Listo cuando:** las hojas sanas no salgan con roya alta, lo que no sea hoja quede avisado y los errores se vean como errores.

### [~] Fase 2: Maduración real (lun 2)
Resultados y límites en `docs/CALIBRACION.md`.

- [x] SAM encuentra cada cereza y la app la clasifica por el color dentro de su máscara.
- [x] Se reemplaza el error 501 actual, y Muse confirma el racimo y explica el conteo.
- [~] Comparar con conteos a mano. Van 6 de 10 racimos, todos dentro del 20 %, con conteo visual sobre la foto.
- [ ] Repetir con racimos reales de Daniel.

**Listo cuando:** en 10 racimos, el conteo no se aleje más de 20 % del conteo a mano.

### [x] Fase 3: Mini chat con Muse (lun 2 por la noche)
Resultados y límites en `docs/CALIBRACION.md`. La batería se repite con `scripts/evaluar_chat.py`.

- [x] Respuestas en streaming, con acceso al último escaneo y al historial del lote.
- [x] Búsqueda con citas para priorizar Cenicafé y la Federación.
- [x] Sin dosis de químicos y remitiendo al extensionista. Se limita a temas de café y finca.
- [ ] Voz, opcional si queda tiempo.

**Listo cuando:** pase una batería de 20 preguntas, incluidas preguntas trampa sobre dosis y temas ajenos.
La voz se agrega solo si esta fase termina a tiempo.

### [x] Fase 4: Identidad Colombia + Meta (mar 3 por la mañana)
- [x] Inicio con el campo colombiano, el flujo por pasos y los nombres de los modelos, en texto.
- [x] Revisar todos los textos y tratar de usted en toda la app.
- [x] Crear con Muse Image la imagen para compartir el enlace (1200×630).
- [ ] Cambiar `og:image` a la URL absoluta cuando exista el dominio (fase 6).
- [ ] Agregar el logo de Meta solo si lo aprueban, en `ConstruidoConMeta`.

**Listo cuando:** alguien entienda en 10 segundos qué hace la app y qué modelos usa.

### [x] Fase 5: Lista para los jueces (mar 3 por la mañana)
- [x] 8 fotos de ejemplo con crédito. Se analizan una sola vez y luego responden al instante, sin gastar créditos.
- [x] Finca de ejemplo claramente marcada, para que el panel no se vea vacío.
- [x] Historial por visitante con cookie anónima.
- [x] Límites por IP y en total por día: análisis 40 y 800, chat 60 y 1500. Se cambian con `ROYALENS_LIMITE_*`.
- [x] Borrado automático a los 30 días, botón "Borrar mis datos" y aviso visible.
- [x] Fotos HEIC de iPhone.
- [ ] Probar los límites detrás del proxy de Coolify (fase 6): la IP se toma del último valor de `X-Forwarded-For`.

**Listo cuando:** dos navegadores distintos no compartan datos y el límite responda con un error claro.

### [ ] Fase 6: Despliegue (mar 3 por la tarde)
- Probar el Dockerfile y subir a Coolify con dominio y HTTPS.
- Configurar la variable `MODEL_API_KEY` y el volumen `/data`.

**Listo cuando:** la cámara en vivo funcione en el celular y el historial sobreviva a un redespliegue.

### [ ] Fase 7: Pruebas finales (mar 3 por la noche)
- Tests del backend y flujos completos en el navegador.
- Móvil y escritorio, API caída, foto pesada y conexión lenta.

**Listo cuando:** no quede ningún error bloqueante y hayamos hecho dos pasadas completas en producción.

### [ ] Fase 8: Video y entrega (mié 4 antes del mediodía)
- Congelar el código, grabar con la app ya desplegada, dejar listo el README y enviar.
- Si el repositorio debe ser público, antes revisar que no tenga secretos.

## Si falta tiempo

Se recorta en este orden: voz, detalles visuales de Inicio y luego la búsqueda con citas. La roya no se recorta.
