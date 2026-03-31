# ============================================================
# theme.py — Sistema de temas compartido
# Importar en cada página: from theme import get_theme, inject_css
# ============================================================

import streamlit as st
import pandas as pd
from pathlib import Path

# ── Diccionarios de tema ──────────────────────────────────────
DARK_THEME = {
    "bg":              "#0d0f14",
    "surface":         "#151820",
    "surface2":        "#1c2030",
    "border":          "#2e3446",
    "text":            "#f0ede6",
    "text2":           "#e0ddd6",
    "muted":           "#b0b8c8",
    "accent":          "#d4a843",
    "accent_alpha08":  "rgba(212,168,67,0.08)",
    "accent_alpha25":  "rgba(212,168,67,0.25)",
    "accent_alpha60":  "rgba(212,168,67,0.6)",
    "negative":        "#e05252",
    "negative_faded":  "rgba(224,82,82,0.5)",
    "neutral":         "#8896aa",
    "positive":        "#4db87a",
    "twitter":         "#4a9edd",
    "youtube":         "#e05252",
}

LIGHT_THEME = {
    "bg":              "#f4f3ef",
    "surface":         "#ffffff",
    "surface2":        "#eceae4",
    "border":          "#d0cfc8",
    "text":            "#1c1c2e",
    "text2":           "#2e2e3e",
    "muted":           "#6b7280",
    "accent":          "#b8860b",
    "accent_alpha08":  "rgba(184,134,11,0.08)",
    "accent_alpha25":  "rgba(184,134,11,0.25)",
    "accent_alpha60":  "rgba(184,134,11,0.6)",
    "negative":        "#c0392b",
    "negative_faded":  "rgba(192,57,43,0.4)",
    "neutral":         "#7f8c9a",
    "positive":        "#27ae60",
    "twitter":         "#2980b9",
    "youtube":         "#c0392b",
}

_CSS_PATH = Path(__file__).parent / "assets" / "style.css"


def setup_theme() -> dict:
    """Renderiza el toggle en el sidebar, aplica el CSS y devuelve T.
    Llamar una sola vez al inicio de cada página."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    with st.sidebar:
        # Leer y escribir session_state explícitamente para que persista entre páginas
        st.session_state.dark_mode = st.toggle(
            "Modo oscuro",
            value=st.session_state.dark_mode,
        )
        st.divider()

    T = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME
    inject_css(T)
    return T


def inject_css(T: dict) -> None:
    """Inyecta las variables CSS del tema + el stylesheet compartido en un único bloque."""
    with open(_CSS_PATH, encoding="utf-8") as f:
        static_css = f.read()

    st.markdown(f"""<style>
:root {{
    --bg:             {T["bg"]};
    --surface:        {T["surface"]};
    --surface2:       {T["surface2"]};
    --border:         {T["border"]};
    --text:           {T["text"]};
    --text2:          {T["text2"]};
    --muted:          {T["muted"]};
    --accent:         {T["accent"]};
    --accent-a08:     {T["accent_alpha08"]};
    --accent-a25:     {T["accent_alpha25"]};
    --accent-a60:     {T["accent_alpha60"]};
    --negative:       {T["negative"]};
    --negative-faded: {T["negative_faded"]};
    --neutral:        {T["neutral"]};
    --positive:       {T["positive"]};
    --twitter:        {T["twitter"]};
    --youtube:        {T["youtube"]};
}}
{static_css}
</style>""", unsafe_allow_html=True)


def make_plotly_layout(T: dict) -> dict:
    """Base layout de Plotly consistente con el tema activo."""
    return dict(
        paper_bgcolor=T["surface"],
        plot_bgcolor=T["surface"],
        font=dict(family="DM Mono, monospace", color=T["muted"], size=14),
        xaxis=dict(gridcolor=T["border"], linecolor=T["border"],
                   tickfont=dict(size=13, color=T["muted"])),
        yaxis=dict(gridcolor=T["border"], linecolor=T["border"],
                   tickfont=dict(size=13, color=T["muted"])),
        hoverlabel=dict(bgcolor=T["surface"], font_size=14,
                        font_family="DM Mono, monospace"),
    )


# ── Hitos compartidos ─────────────────────────────────────────
MILESTONES = [
    ("2020-06", "GPT-3"),
    ("2021-01", "DALL-E"),
    ("2022-11", "ChatGPT"),
    ("2023-03", "GPT-4"),
    ("2023-12", "Gemini"),
    ("2024-03", "EU AI Act"),
]


def add_milestone_lines(fig, x_min, x_max, T: dict,
                        line_color: str = None, text_color: str = None,
                        show_legend: bool = False):
    """Añade líneas verticales de hitos a una figura Plotly.

    Args:
        line_color: color de la línea (por defecto accent_alpha60 del tema).
        text_color: color del texto de la anotación (por defecto accent del tema).
        show_legend: si True, añade una anotación compacta en la esquina
                     superior derecha con la lista de hitos.
    """
    lc = line_color or T["accent_alpha60"]
    tc = text_color or T["accent"]

    positions = ["top left", "top right"]
    visible = [(ms, lbl) for ms, lbl in MILESTONES
               if x_min <= pd.Timestamp(ms) <= x_max]

    for i, (month_str, label) in enumerate(visible):
        ts = pd.Timestamp(month_str)
        fig.add_vline(
            x=ts.timestamp() * 1000,
            line_width=1,
            line_dash="dot",
            line_color=lc,
            annotation_text=label,
            annotation_position=positions[i % 2],
            annotation_font=dict(size=14, color=tc,
                                 family="DM Mono, monospace"),
        )

    if show_legend:
        lines = [f"● {lbl} &nbsp;{mo}" for mo, lbl in MILESTONES]
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.99, y=0.99,
            xanchor="right", yanchor="top",
            text="<br>".join(lines),
            showarrow=False,
            font=dict(size=10, color=tc, family="DM Mono, monospace"),
            align="right",
            bgcolor=T["surface"],
            bordercolor=T["border"],
            borderwidth=1,
            borderpad=8,
            opacity=0.88,
        )
    return fig
