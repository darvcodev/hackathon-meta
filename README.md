# RoyaLens

![Vista previa de RoyaLens](frontend/public/img/compartir.jpg)

**RoyaLens** ayuda a revisar hojas y racimos de café desde el celular. Estima qué parte de una hoja está afectada por roya, cuenta cerezas visibles por estado de maduración y guarda los resultados por lote. Un asistente explica los escaneos y responde preguntas sobre el cafetal.

La aplicación está impulsada por **SAM 3.1 y Muse Spark de Meta**. SAM entrega máscaras de imagen; el porcentaje y los conteos los calcula el código de RoyaLens a partir de esas máscaras. Son estimaciones de una foto, no mediciones de campo certificadas.

## La aplicación

![Inicio de RoyaLens](readme-assets/inicio.webp)

*Inicio de la aplicación. La foto del cafetal forma parte de la interfaz.*

![Panel de finca en modo demo](readme-assets/finca-demo.webp)

*Panel con datos ilustrativos. En una sesión nueva se identifica como «Finca de ejemplo» y se reemplaza por los escaneos del visitante.*

La interfaz incluye cámara, escáner de roya, maduración, panel por lotes y asistente. Hay ocho fotos de ejemplo con créditos visibles para probar los flujos sin una finca cerca.

## Cómo funciona el análisis

```mermaid
flowchart LR
    A[Foto del celular] --> B[FastAPI]
    B --> C[Preparación de imagen]
    C --> D[SAM 3.1: máscaras]
    D --> E[RoyaLens: filtros, área y conteos]
    E --> F[Muse Spark: interpretación]
    F --> G[Resultado y avisos]
    G --> H[SQLite y fotos por visitante]
```

### Roya

1. Se reduce la imagen cuando supera el tamaño de trabajo y se envía a SAM 3.1. Una solicitud busca la hoja y otras buscan posibles manchas. Si el primer prompt no encuentra una hoja, se usa uno de respaldo.
2. Se elige una hoja principal, grande y cercana al centro. Las manchas fuera de ella o con color incompatible con roya se descartan. Las máscaras aceptadas se unen para no contar dos veces los píxeles solapados.
3. RoyaLens calcula `píxeles de lesión dentro de la hoja / píxeles de hoja × 100`. También cuenta las lesiones y asigna una clase de severidad orientativa.
4. Muse Spark ve la foto junto con la medición y devuelve una explicación estructurada. Si no se reconoce una hoja medible, la foto parece inadecuada o Muse no confirma el contexto, la app muestra avisos y evita sumar una cifra engañosa al lote.

### Maduración

1. SAM 3.1 busca frutos redondos en la foto completa y en cuatro recortes. El análisis reúne las máscaras y elimina duplicados.
2. RoyaLens examina el color dentro de cada máscara para clasificar las cerezas visibles como **verdes, pintonas, maduras o sobremaduras**. El porcentaje sale del conteo, no de Muse Spark.
3. Muse Spark confirma si la escena parece un racimo de café y explica el resultado. Si hay muy pocas cerezas o están demasiado lejos, se pide repetir la foto y ese porcentaje no entra al panel.

### Asistente y panel

El asistente recibe el historial del visitante como contexto y transmite la respuesta por partes. Puede consultar la web y presenta las fuentes cuando están disponibles. La conversación se guarda en la sesión del navegador; el servidor no mantiene un historial de chats. El panel agrega escaneos válidos por lote para mostrar historial, incidencia sobre las hojas fotografiadas, evolución y alertas.

Los límites del método están resumidos en [HACKATHON.md](HACKATHON.md). En particular, falta contrastar los porcentajes con mediciones de un agrónomo y ampliar las pruebas con fotos de campo colombiano.

## Arquitectura del repositorio

| Ruta | Función |
|---|---|
| `frontend/src/pages/` | Las seis pantallas de React |
| `frontend/src/components/ui.jsx` | Componentes, navegación y avisos compartidos |
| `frontend/src/api.js` | Solicitudes a la API y lectura del stream del asistente |
| `backend/main.py` | Rutas FastAPI, validación de archivos, cookie de visitante y entrega del frontend |
| `backend/service.py` | Orquestación de los análisis real y demo |
| `backend/store.py` | SQLite, historial, fotos, límites de uso y retención |
| `backend/chat.py`, `backend/ejemplos.py` | Asistente y catálogo de fotos de ejemplo |
| `royalens/royalens/meta_api.py` | Llamadas a SAM 3.1 y Muse Spark mediante Meta Model API |
| `royalens/royalens/analysis.py` | Filtros, máscaras, porcentajes, conteos y anotaciones |
| `royalens/royalens/pipeline.py` | Flujos completos de roya y maduración |
| `backend/tests/`, `royalens/tests/` | Pruebas sin llamadas de pago a los modelos |
| `scripts/` | Evaluaciones opcionales con fotos locales; consumen créditos de API |

El frontend se compila con Vite. En producción, FastAPI sirve la compilación y la API desde un solo contenedor. SQLite y las fotos se guardan en `/data` cuando se usa Docker.

## Desarrollo local

Se necesitan Python 3.12, `uv` y Node.js 22.

```bash
make setup
make backend
```

En otra terminal:

```bash
make frontend
```

Abra `http://localhost:5173`. `make backend` inicia el **modo demo**: usa segmentación local por color, no llama a Meta y marca los resultados como demostración. El asistente requiere el modo real.

Para usar los modelos, copie `royalens/.env.example` a `royalens/.env`, defina `MODEL_API_KEY` y ejecute `make backend-real`. El archivo `.env` está excluido de Git.

## API

| Método y ruta | Uso |
|---|---|
| `GET /api/estado` | Modo activo y lotes disponibles |
| `POST /api/roya` | Analizar una hoja (`foto`, `lote`) |
| `POST /api/maduracion` | Analizar un racimo (`foto`, `lote`) |
| `GET /api/ejemplos/{tipo}` | Listar fotos de ejemplo de roya o maduración |
| `POST /api/ejemplos/{slug}` | Analizar o reutilizar un ejemplo |
| `GET /api/escaneos/{id}` | Leer un escaneo del visitante |
| `GET /api/resumen` | Panel del visitante |
| `POST /api/chat` | Respuesta del asistente en NDJSON |
| `DELETE /api/mis-datos` | Borrar los escaneos del visitante |

Las imágenes originales y anotadas se entregan por `/media/{nombre}` tras comprobar la cookie y la propiedad del escaneo.

## Datos y despliegue

El `Dockerfile` compila React y arranca FastAPI en el puerto **8000** y en **modo real**. Para desplegar, configure `MODEL_API_KEY` como secreto, HTTPS para la cámara y un volumen persistente en `/data`. El health check consulta `/api/estado`. La [guía del hackathon](HACKATHON.md) contiene la revisión posterior al despliegue.

Cada navegador recibe una cookie anónima. Los escaneos se separan por visitante y por modo; las fotos se eliminan junto con el escaneo al usar «Borrar mis datos» o al vencer la retención de 30 días. Los límites diarios de análisis y chat se configuran con las variables `ROYALENS_LIMITE_*`. Las ocho fotos de ejemplo comparten un resultado de análisis almacenado para evitar llamadas repetidas a la API.

## Verificación

```bash
make test
make build
```

Las pruebas usan respuestas simuladas de los modelos y no consumen créditos. Los scripts de `scripts/` permiten repetir evaluaciones con fotos locales en `fotos/`; esa carpeta está excluida del repositorio porque contiene imágenes de terceros usadas para calibrar.

## Créditos de imágenes

Los enlaces, autores y licencias de las fotos de ejemplo están en `backend/ejemplos.py` y se muestran junto a cada ejemplo en la app. Las imágenes marcadas como generadas se identifican como tales. El [símbolo de Meta](https://commons.wikimedia.org/wiki/File:Meta_Platforms_logo.svg) se usa con la autorización confirmada por el responsable del proyecto.
