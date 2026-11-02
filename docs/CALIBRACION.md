# Calibración

Primera ronda: 2026-11-01. Se repite con `scripts/evaluar_roya.py` y `scripts/evaluar_maduracion.py`, que gastan créditos.

# Roya

## Qué se decidió

| Decisión | Valor | Por qué |
|---|---|---|
| Prompts de lesión | `orange rust spot` + `orange patch` | El primero separa pústulas y el segundo agrega zonas grandes. `coffee rust lesion` casi no detectó nada. |
| Filtro de color | Tono 10–75°, saturación ≥ 0,30 | Manchas de otra enfermedad: saturación ≤ 0,19. Pústulas de roya: ≥ 0,36. La confianza de SAM no las separaba. |
| Hoja medida | La más grande y central | Sumar todas las hojas de la foto diluía el porcentaje. |
| Hoja mínima | 8 % de la foto | Más lejos no hay detalle suficiente; la foto no se cuenta en el lote. |
| Foto mala | No se cuenta | Muse la califica; no sirve para dar una hoja por sana. |
| Haz sin lesiones | No se cuenta | Según Cenicafé, las pústulas salen en el envés; por el haz no se puede dar la hoja por sana. |

## Escala

- **Fuente:** [Diagrama de Área Estándar de Cenicafé, Avances Técnicos 498, 2018](https://biblioteca.cenicafe.org/bitstream/10778/4244/1/avt0498.pdf).
- **Intervalos de Cenicafé:** 0,05–1,4 / 1,5–2,9 / 3–5,9 / 6–11,9 / 12–23,9 / 24–47,9 / 48–80 %, con marcas de 1, 2, 4, 8, 16, 32 y 64 %.
- **Niveles de RoyaLens:** Sin roya visible (< 0,05), Leve (< 3), Moderada (< 12), Alta (< 24) y Severa (≥ 24).
  Los límites salen de esos intervalos, pero **los nombres son nuestros y no están validados por un agrónomo**.
- **Lote:** incidencia = hojas con roya / hojas evaluadas; severidad = suma de porcentajes / hojas evaluadas, como en el mismo documento.
  Cenicafé evalúa 50 árboles por lote, así que la cifra de la app es orientativa.
- **Referencia nacional:** el [Boletín 18, primer trimestre de 2026](https://publicaciones.cenicafe.org/index.php/fitosanitario/article/download/4996/5598/4313) reporta 4,5 % de incidencia promedio.

## Resultado

Las 14 fotos de la última corrida cumplen el criterio de `scripts/evaluar_roya.py`. Muse no siempre es igual entre corridas: la misma foto puede cambiar de calidad "regular" a "mala".

| Foto | Medición | Muse: ¿signos de roya? |
|---|---|---|
| `roya_01` | 25,2 %, Severa | Sí |
| `roya_02` | 9,4 %, Moderada | Sí |
| `roya_03` | 1,9 %, Leve | Sí |
| `roya_04` | 16,2 %, Alta | Sí |
| `roya_05` (acercamiento extremo) | Sin medición | Sí |
| `sana_01` | 0 % | No |
| `sana_02` (planta entera, lejos) | Sin medición | No |
| `otra_enfermedad_01` y `_02` | 0 %, manchas descartadas por color | No |
| `mala_01` a `_05` | Sin medición | No |
| `no_hoja_01` a `_04` y `_06` | Sin medición | No |

## Estabilidad

La misma foto con cambios de luz, desenfoque, rotación y compresión:

| Foto | Original | Oscura | Clara | Borrosa | Rotada | Comprimida |
|---|---|---|---|---|---|---|
| `roya_01` | 25,2 | 18,3 | 20,3 | 25,4 | 25,5 | 25,0 |
| `roya_04` | 16,2 | 16,0 | 26,4 | 25,8 | 15,0 | 27,0 |

La cifra puede moverse hasta unos 10 puntos, o una clase del diagrama. Por eso la interfaz dice "estimado".

## Límites conocidos

- **Muestra pequeña:** 14 fotos, y los umbrales se ajustaron con esas mismas fotos, así que el 14 de 14 no prueba precisión general.
- **Sin referencia exacta:** ninguna foto tiene un porcentaje medido por un experto; la revisión de las máscaras fue visual.
- **Polvillo difuso:** se subestima. En `roya_04` la zona de polvo disperso no siempre queda marcada.
- **Manchas amarillas iniciales:** algunas no se miden, como las de la hoja derecha de `roya_03`.
- **Varias hojas:** solo se mide una; en `roya_03` la elegida no es la más afectada.
- **Fotos de otras regiones:** las fotos de prueba no son de fincas colombianas.
- **Metas de la fase 1 sin completar:** roya 5 de 10 y sanas 2 de 5. Ya se cumplen no hoja (5) y malas (5).

# Maduración

## Qué se decidió

| Decisión | Valor | Por qué |
|---|---|---|
| Prompt | `round fruit` | `coffee cherry`, `coffee berry` y `cherry` devolvieron 0 en las fotos reales. |
| Búsqueda | Foto completa + 4 cuadrantes | En una rama cargada pasó de 32 a 98–104 cerezas. Son 5 peticiones a SAM y 1 a Muse por foto. |
| Estado | Color dentro de la máscara | Rojo ≥ 60 %: maduro, o sobremaduro si la mayoría es oscura. Verde ≥ 60 %: verde. El resto: pintón. |
| Filtro de fondo | Menos de 30 % del tamaño típico | Quita frutos diminutos fuera de foco. |
| Tamaño mínimo | 0,05 % de la foto por cereza | Por debajo se tomó la planta entera, no un racimo. |
| Mínimo | 5 cerezas | Con menos, el porcentaje no representa al racimo. |
| Confirmación | Muse dice si es un racimo en la rama | SAM encuentra cualquier fruto redondo. Rechazó café en costal, en secado y cerezas sueltas. |

La recomendación principal es una regla fija sobre el conteo. Muse la explica en lenguaje de finca, sin poder cambiar las cifras.

## Resultado

| Foto | App | Conteo visual | Diferencia | Verde / Pintón / Maduro / Sobremaduro |
|---|---|---|---|---|
| `racimo_01` | 32 | 38 | −16 % | 22 / 1 / 9 / 0 |
| `racimo_02` | 42 | 47 | −11 % | 22 / 3 / 9 / 8 |
| `racimo_04` | 31 | 34 | −9 % | 0 / 0 / 25 / 6 |
| `racimo_05` | 6 | 6 | 0 % | 0 / 1 / 5 / 0 |
| `racimo_06` | 43 | 40 | +8 % | 38 / 5 / 0 / 0 |
| `racimo_10` (generada) | 28 | 30 | −7 % | 7 / 3 / 12 / 6 |
| `racimo_07` (muy densa) | 98 | Sin contar | — | 13 / 10 / 58 / 17 |

Las 20 fotos de la última corrida completa cumplieron el criterio: 7 racimos y 13 casos que debían rechazarse.

## Límites conocidos

- **Conteo a mano:** es visual y sobre la foto, no en campo, y lo hizo Claude. Las cerezas escondidas no se ven en ningún caso.
- **Muestra pequeña:** 6 fotos con conteo y 7 racimos, frente a la meta de 10.
- **Sombra:** una cereza roja en sombra puede salir como sobremadura; el tono no las separa. En `racimo_02` hay más sobremaduras de las que parece a simple vista.
- **Variedades amarillas:** una cereza amarilla madura sale como pintón. Muse puede advertirlo, pero no cambia el conteo.
- **Falsos positivos:** en `racimo_06` hay algunos frutos secos y oscuros contados como cerezas.
- **Memoria:** las máscaras de 5 peticiones se guardan a tamaño completo; hay que revisar el consumo en el servidor durante la fase 6.

# Asistente

## Qué se decidió

| Decisión | Valor | Por qué |
|---|---|---|
| Modelo | Muse Spark 1.3, en streaming | El primer texto aparece en unos 4 segundos en promedio. |
| Datos de la finca | Se le entregan desde la base de datos | Así no inventa cifras: si un lote no tiene escaneos, lo dice. |
| Base verificada | Avances Técnicos 498 y Boletín 18 de Cenicafé | Sin ella, atribuía a Cenicafé cifras tomadas de otras páginas. |
| Búsqueda web | Solo si la base no alcanza | Con el dato de la web, las citas de Muse no siempre aparecen. |
| Fuentes | Citas de Muse o, si no hay, páginas consultadas | Una página consultada no prueba cada frase, por eso se rotula distinto. |
| Dosis y marcas | Instrucción más filtro en el servidor | Si aparece una dosis o una marca, se reemplaza la respuesta. |
| Conversación | La guarda el navegador, no el servidor | No hace falta cuenta ni base de datos de chats. |

## Resultado

21 de 21 preguntas sin fallos evidentes, sobre una finca con datos de prueba: datos de la finca, conocimiento técnico, inglés, búsqueda web y trampas.
Se leyeron las respuestas, no solo las reglas automáticas. Tiempo medio total: 5,7 segundos; máximo con búsqueda: 20,5 segundos en la batería y unos 30 en el navegador.

## Límites conocidos

- **Filtro de dosis:** cubre formas comunes y una lista corta de productos, no todas las posibles. Como actúa durante el streaming, una dosis podría verse un instante antes de reemplazarse.
- **Muse varía:** la batería pasó en dos corridas, pero no garantiza que siempre responda igual.
- **Precios:** los resultados de búsqueda fueron flojos, incluido un video corto. Ahora solo debe dar cifras de la Federación; no hay garantía de que encuentre el dato.
- **Sin revisión experta:** ningún agrónomo ha leído estas respuestas.
- **Sin voz:** no se agregó la entrada por voz, que el plan dejaba como opcional.
