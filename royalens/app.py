"""Interfaz web de RoyaLens. Ejecuta:  python app.py  y abre http://127.0.0.1:7860"""

from __future__ import annotations

import html
import json

import gradio as gr

from royalens import config
from royalens.meta_api import MissingApiKey
from royalens.pipeline import analyze


def _severity_card(d) -> str:
    s = d.severity
    warn = "".join(f"<li>{html.escape(w)}</li>" for w in d.warnings)
    warn_html = f"<ul class='rl-warn'>{warn}</ul>" if warn else ""
    return f"""
<div class="rl-card" style="border-left:8px solid {s.color}">
  <div class="rl-pct" style="color:{s.color}">{s.percent:.1f}%</div>
  <div class="rl-level">Severidad: <b>{html.escape(s.level)}</b></div>
  <div class="rl-meta">{s.lesion_count} lesiones detectadas sobre la hoja</div>
  {warn_html}
  <div class="rl-note">Escala orientativa de la demo. Confirma el diagnóstico con tu extensionista.</div>
</div>"""


def _muse_markdown(muse: dict) -> str:
    if "_sin_formato" in muse:
        return muse["_sin_formato"]
    if muse.get("es_hoja_de_cafe") is False:
        return "### La foto no parece una hoja de café\nToma una foto de una sola hoja, de cerca y con buena luz."
    parts = ["### Lo que ve la IA", muse.get("lo_que_se_ve", "")]
    otras = muse.get("otras_causas_posibles") or []
    if otras:
        parts += ["**Podría confundirse con:** " + ", ".join(otras)]
    parts += ["### Recomendación", muse.get("recomendacion", "")]
    if muse.get("consejo_foto"):
        parts += ["*Consejo para la foto:* " + muse["consejo_foto"]]
    return "\n\n".join(p for p in parts if p)


async def run(image, lesion_prompts_text, min_conf):
    if image is None:
        raise gr.Error("Sube o toma una foto de una hoja de café.")
    prompts = [p for p in lesion_prompts_text.split(",") if p.strip()]
    try:
        d = await analyze(image, prompts, float(min_conf))
    except MissingApiKey as e:
        raise gr.Error(str(e))
    except Exception as e:  # error técnico: nunca se presenta como diagnóstico
        raise gr.Error(f"Error al llamar a la API de Meta: {e}")
    return (
        d.overlay,
        _severity_card(d),
        _muse_markdown(d.muse),
        json.dumps(d.as_dict(), ensure_ascii=False, indent=2),
    )


CSS = """
.rl-card{padding:16px 20px;border-radius:12px;background:var(--block-background-fill)}
.rl-pct{font-size:56px;font-weight:800;line-height:1}
.rl-level{font-size:20px;margin-top:6px}
.rl-meta{opacity:.8;margin-top:4px}
.rl-warn{color:#c62828;margin:10px 0 0 18px}
.rl-note{font-size:12px;opacity:.65;margin-top:10px}
"""

with gr.Blocks(title="RoyaLens", css=CSS, theme=gr.themes.Soft(primary_hue="green")) as demo:
    gr.Markdown(
        "# ☕ RoyaLens\n"
        "Toma una foto de una hoja de café. **SAM 3.1** recorta la hoja y cada mancha de roya, "
        "la app **mide qué porcentaje de la hoja está afectado**, y **Muse Spark** lo explica "
        "en lenguaje sencillo."
    )
    with gr.Row():
        with gr.Column():
            image_in = gr.Image(type="pil", sources=["upload", "webcam"], label="Hoja de café")
            with gr.Accordion("Ajustes avanzados", open=False):
                prompts_in = gr.Textbox(
                    value=", ".join(config.DEFAULT_LESION_PROMPTS),
                    label="Qué buscar como lesión (frases separadas por coma, en inglés)",
                )
                conf_in = gr.Slider(0.0, 1.0, value=config.MIN_CONFIDENCE, step=0.05,
                                    label="Confianza mínima de SAM")
            btn = gr.Button("Analizar hoja", variant="primary")
        with gr.Column():
            overlay_out = gr.Image(label="Hoja (verde) y lesiones (naranja)")
            card_out = gr.HTML()
            muse_out = gr.Markdown()
            with gr.Accordion("Datos técnicos", open=False):
                json_out = gr.Code(language="json")

    btn.click(run, [image_in, prompts_in, conf_in], [overlay_out, card_out, muse_out, json_out])

if __name__ == "__main__":
    demo.launch()
