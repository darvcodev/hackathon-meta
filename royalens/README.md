# ☕ RoyaLens

**Diagnóstico de roya del café con una foto del celular.**
Proyecto para el Meta Global AI Developer Hackathon (track Indie, tema *Build for Your World*).

La roya (*Hemileia vastatrix*) es la enfermedad más dañina del café en Colombia. Detectarla a
tiempo y saber **qué tan avanzada está** decide si un lote necesita manejo. Hoy eso depende de
que un técnico visite la finca. RoyaLens lo hace con una foto.

## Cómo funciona

1. **SAM 3.1** recorta la hoja (`"coffee leaf"`) y, en paralelo, cada mancha de roya
   (`"orange rust spot"`). Devuelve máscaras exactas, píxel por píxel.
2. La app **mide**: porcentaje del área de la hoja cubierta por lesiones y número de lesiones.
   Ese número sale de las máscaras, no de un modelo de lenguaje.
3. **Muse Spark 1.3** mira la foto junto con la medición y explica en lenguaje sencillo qué se
   ve, con qué podría confundirse y qué hacer. No da dosis de químicos: remite al extensionista.
4. La interfaz muestra la hoja con contorno verde, las lesiones en naranja y el nivel de severidad.

Si la foto no es una hoja de café, Muse lo detecta y la app no da diagnóstico.
Un error de la API se muestra como error, nunca como resultado.

## Arranque (5 minutos)

```bash
pip install -r requirements.txt
cp .env.example .env        # y pega tu API key de https://dev.meta.ai/
python app.py               # abre http://127.0.0.1:7860
```

Prueba por terminal con una sola foto:

```bash
python analyze.py fotos/hoja1.jpg
```

Pruebas sin API (no gastan créditos):

```bash
python -m pytest -q
```

## Estructura

| Archivo | Qué hace |
|---|---|
| `royalens/config.py` | Modelos, frases de búsqueda, confianza mínima y escala de severidad |
| `royalens/meta_api.py` | Llamadas a SAM 3.1 y Muse Spark según la documentación oficial |
| `royalens/analysis.py` | Medición de área, conteo de lesiones y dibujo de la imagen anotada |
| `royalens/pipeline.py` | Une todo el flujo |
| `app.py` | Interfaz web (Gradio) |
| `analyze.py` | Prueba por terminal |
| `tests/` | Pruebas con respuestas de SAM simuladas |

## Límites conocidos

- La escala de severidad es **orientativa** (`config.SEVERITY_LEVELS`); falta validarla con un
  agrónomo o con las escalas diagramáticas de Cenicafé.
- La frase `"orange rust spot"` hay que ajustarla con fotos reales: se puede cambiar desde
  *Ajustes avanzados* sin tocar código.
- Funciona mejor con una hoja por foto, de cerca, con luz natural y mostrando el envés,
  que es donde aparece el polvillo naranja.
