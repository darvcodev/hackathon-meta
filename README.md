# RoyaLens

App web para caficultores colombianos. Con una foto del celular mide la roya en cada hoja
y la maduración de cada racimo, y guarda todo en un panel por lotes.

## Estructura

| Carpeta | Contenido |
|---|---|
| `frontend/` | React, Vite, Tailwind y Framer Motion. Imágenes en `public/img/` |
| `backend/` | FastAPI, modo demo e historial en SQLite |
| `royalens/` | Núcleo de análisis con SAM 3.1 y Muse Spark |
| `mockups/` | Diseños aprobados, solo de referencia |

## Arrancar

```bash
make setup
```

En una terminal:

```bash
make backend
```

En otra terminal:

```bash
make frontend
```

La app queda en http://localhost:5173.

## Modos

- **Demo** (`make backend`): segmenta por color en tu equipo, no usa la API ni gasta créditos.
  Los resultados no son un diagnóstico y la interfaz los marca como demo.
- **Real** (`make backend-real`): usa SAM 3.1 y Muse Spark. Requiere `MODEL_API_KEY` en `royalens/.env`.
  La maduración real todavía no está conectada y responde con error.

Los datos de cada modo no se mezclan.

## Pruebas

```bash
make test
```

## Despliegue

Un solo contenedor con el `Dockerfile`. En Coolify, define `MODEL_API_KEY` y monta un volumen en `/data`.
