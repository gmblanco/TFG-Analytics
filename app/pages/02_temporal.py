# ============================================================
# pages/02_temporal.py — Evolución Temporal del Sentimiento
# H1: Polarización creciente post-ChatGPT
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from theme import setup_theme, make_plotly_layout, add_milestone_lines, MILESTONES

# ── Rutas ─────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "processed"
YT_PATH  = DATA_DIR / "youtube_sentiment_v2.parquet"

# ── Tema ──────────────────────────────────────────────────────
T             = setup_theme()
PLOTLY_LAYOUT = make_plotly_layout(T)

# ── Carga ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos…")
def load_yt():
    df = pd.read_parquet(YT_PATH)
    df["date"]          = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["comment_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year"]          = df["date"].dt.year
    df["fase"]          = df["year"].apply(
        lambda y: "Pre-ChatGPT" if y <= 2022 else "Era ChatGPT"
    )
    return df

try:
    yt = load_yt()
except FileNotFoundError as e:
    st.error(f"Parquet no encontrado.\n\n`{e}`")
    st.stop()

# ── Cabecera ──────────────────────────────────────────────────
st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;'
    f'letter-spacing:0.15em;color:{T["accent"]};text-transform:uppercase;'
    f'margin-bottom:6px">H1 · Evolución temporal</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<h1 style="font-size:clamp(24px,3vw,34px);font-weight:900;'
    f'color:{T["text"]};margin-bottom:8px;line-height:1.15">'
    f'Cómo cambia el tono del discurso sobre IA mes a mes</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="color:{T["muted"]};font-size:16px;margin-bottom:24px;line-height:1.6">'
    f'Sentimiento mensual en YouTube (2020–2026). '
    f'Las líneas verticales marcan lanzamientos de modelos y eventos regulatorios.</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Series mensuales ──────────────────────────────────────────
monthly = (
    yt.groupby(["comment_month", "sentiment_label"])
    .size()
    .unstack(fill_value=0)
)
monthly_pct = monthly.div(monthly.sum(axis=1), axis=0) * 100
monthly_pct.index = pd.to_datetime(monthly_pct.index)

x_min = monthly_pct.index.min()
x_max = monthly_pct.index.max()

# ════════════════════════════════════════════════════════════
#  GRÁFICO 1 — Sentimiento mensual con pestañas
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:19px;'
    f'font-weight:700;color:{T["text"]};margin-bottom:4px">'
    f'Sentimiento mensual — YouTube 2020–2026</p>'
    f'<p style="font-family:\'DM Mono\',monospace;font-size:13px;'
    f'color:{T["muted"]};margin-bottom:12px">'
    f'Sin suavizado · valores reales mensuales</p>',
    unsafe_allow_html=True,
)

# Colores de hitos según tema
if st.session_state.dark_mode:
    m_line  = T["accent_alpha60"]
    m_color = T["accent"]
else:
    m_line  = "rgba(210,60,50,0.55)"
    m_color = "#d43c30"

# Leyenda de hitos — esquina superior derecha, 3+3
def _milestone_item(mo, lbl, color, muted):
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px">'
        f'<span style="color:{color};font-size:13px">●</span>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:11px;color:{muted}">'
        f'{lbl} {mo}</span></span>'
    )

row1 = MILESTONES[:3]
row2 = MILESTONES[3:]

def _legend_row(items, color, muted):
    return (
        f'<div style="display:flex;justify-content:flex-end;gap:20px;margin-bottom:4px">'
        + "".join(_milestone_item(mo, lbl, color, muted) for mo, lbl in items)
        + "</div>"
    )

st.markdown(
    _legend_row(row1, m_color, T["muted"]) + _legend_row(row2, m_color, T["muted"]),
    unsafe_allow_html=True,
)

SENT_TABS = [
    ("Negativo", "negative", T["negative"], [20, 75]),
    ("Neutro",   "neutral",  T["neutral"],  [0,  60]),
    ("Positivo", "positive", T["positive"], [0,  45]),
]

tab_neg, tab_neu, tab_pos = st.tabs([s[0] for s in SENT_TABS])

for tab, (label, col_name, color, y_range) in zip(
    [tab_neg, tab_neu, tab_pos], SENT_TABS
):
    with tab:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_pct.index,
            y=monthly_pct[col_name].round(1),
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=3, color=color),
            name=label,
            hovertemplate=f"%{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
        ))
        add_milestone_lines(fig, x_min, x_max, T,
                            line_color=m_line, text_color=m_color)
        fig.update_layout(**{
            **PLOTLY_LAYOUT,
            "height": 360,
            "showlegend": False,
            "yaxis": dict(range=y_range, ticksuffix="%",
                          gridcolor=T["border"], tickfont=dict(size=13, color=T["muted"])),
            "xaxis": dict(gridcolor="rgba(0,0,0,0)",
                          tickfont=dict(size=12, color=T["muted"]), tickformat="%b %Y"),
            "margin": dict(l=10, r=10, t=40, b=10),
        })
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  GRÁFICO 2 — Los tres sentimientos
# ════════════════════════════════════════════════════════════
st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:19px;'
    f'font-weight:700;color:{T["text"]};margin-bottom:12px">'
    f'Distribución mensual del sentimiento en comentarios sobre IA (2020–2026)</p>',
    unsafe_allow_html=True,
)

fig2 = go.Figure()
for col_name, label, color in [
    ("negative", "Negativo", T["negative"]),
    ("neutral",  "Neutral",  T["neutral"]),
    ("positive", "Positivo", T["positive"]),
]:
    if col_name in monthly_pct.columns:
        fig2.add_trace(go.Scatter(
            x=monthly_pct.index,
            y=monthly_pct[col_name].round(1),
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=2.5, color=color),
            hovertemplate=f"{label} %{{x|%b %Y}}: %{{y:.1f}}%<extra></extra>",
        ))

fig2.update_layout(**{
    **PLOTLY_LAYOUT,
    "height": 420,
    "showlegend": True,
    "legend": dict(
        orientation="h",
        yanchor="top",
        y=-0.20,
        xanchor="center",
        x=0.5,
        font=dict(size=15, color=T["text"], family="DM Sans, sans-serif"),
    ),
    "yaxis": dict(
        range=[0, 80],
        ticksuffix="%",
        gridcolor=T["border"],
        tickfont=dict(size=13, color=T["muted"])
    ),
    "xaxis": dict(
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(size=12, color=T["muted"]),
        tickformat="%b %Y",
        automargin=True
    ),
    "margin": dict(l=10, r=10, t=20, b=110),
})
st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  KPIs — Pre vs Era ChatGPT
# ════════════════════════════════════════════════════════════
pre  = yt[yt["fase"] == "Pre-ChatGPT"]
post = yt[yt["fase"] == "Era ChatGPT"]

pre_neg  = (pre["sentiment_label"]  == "negative").mean() * 100
post_neg = (post["sentiment_label"] == "negative").mean() * 100
pre_pos  = (pre["sentiment_label"]  == "positive").mean() * 100
post_pos = (post["sentiment_label"] == "positive").mean() * 100

pre_years  = "2020–2022"
post_years = "2023–2026"

st.markdown(
    f'<p style="font-family:\'Playfair Display\',serif;font-size:19px;'
    f'font-weight:700;color:{T["text"]};margin-bottom:14px">'
    f'Comparación agregada por periodo: etapa pre-ChatGPT frente a era ChatGPT</p>',
    unsafe_allow_html=True,
)

def kpi_card(container, metric_label, value, label_color, delta=None, delta_label="", invert=False):
    delta_html = ""
    if delta is not None:
        d_color = T["negative"] if (delta > 0) == invert else T["positive"]
        arrow   = "↑" if delta > 0 else "↓"
        delta_html = (
            f'<p style="font-size:13px;color:{d_color};margin:0">'
            f'{arrow} {abs(delta):.1f} pp {delta_label}</p>'
        )

    container.markdown(
        f'<div style="background:{T["surface"]};border:1px solid {T["border"]};'
        f'border-radius:12px;padding:18px 18px;min-height:140px;height:100%">'
        f'<p style="font-family:\'DM Mono\',monospace;font-size:11px;'
        f'letter-spacing:0.10em;color:{label_color};text-transform:uppercase;'
        f'margin-bottom:8px">{metric_label}</p>'
        f'<p style="font-family:\'Playfair Display\',serif;font-size:34px;'
        f'font-weight:900;color:{T["text"]};line-height:1;margin-bottom:10px">'
        f'{value:.1f}%</p>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

# Estructura visual: bloque izquierdo | separador | bloque derecho
left_block, divider, right_block = st.columns([1, 0.06, 1])

with left_block:
    st.markdown(
        f'<div style="margin-bottom:12px;padding:10px 14px;border:1px solid {T["border"]};'
        f'border-left:4px solid {T["muted"]};border-radius:10px;background:{T["surface"]}">'
        f'<p style="margin:0;font-family:\'DM Mono\',monospace;font-size:11px;'
        f'letter-spacing:0.12em;color:{T["muted"]};text-transform:uppercase">'
        f'Pre-ChatGPT</p>'
        f'<p style="margin:4px 0 0 0;font-size:14px;color:{T["text"]}">{pre_years}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    l1, l2 = st.columns(2)
    kpi_card(l1, "Sentimiento negativo", pre_neg, T["negative"])
    kpi_card(l2, "Sentimiento positivo", pre_pos, T["positive"])

with divider:
    st.markdown(
        f'<div style="height:100%;min-height:190px;display:flex;justify-content:center;">'
        f'<div style="width:1px;background:{T["border"]};height:100%"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with right_block:
    st.markdown(
        f'<div style="margin-bottom:12px;padding:10px 14px;border:1px solid {T["border"]};'
        f'border-left:4px solid {T["accent"]};border-radius:10px;background:{T["surface"]}">'
        f'<p style="margin:0;font-family:\'DM Mono\',monospace;font-size:11px;'
        f'letter-spacing:0.12em;color:{T["accent"]};text-transform:uppercase">'
        f'Era ChatGPT</p>'
        f'<p style="margin:4px 0 0 0;font-size:14px;color:{T["text"]}">{post_years}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    r1, r2 = st.columns(2)
    kpi_card(
        r1,
        "Sentimiento negativo",
        post_neg,
        T["negative"],
        delta=post_neg - pre_neg,
        delta_label="vs etapa pre-ChatGPT",
        invert=True,
    )
    kpi_card(
        r2,
        "Sentimiento positivo",
        post_pos,
        T["positive"],
        delta=post_pos - pre_pos,
        delta_label="vs etapa pre-ChatGPT",
        invert=False,
    )

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;color:{T["muted"]}">'
    f'Fuente: youtube_sentiment_v2.parquet · '
    f'{len(yt):,} comentarios · 2020–2026 · '
    f'Modelo: cardiffnlp/twitter-xlm-roberta-base-sentiment</p>',
    unsafe_allow_html=True,
)
