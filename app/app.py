# ============================================================
# app.py — Dashboard TFG: Percepción Pública de la IA
# Guadalupe Martínez Blanco · GITT + BA · 2025
#
# Página 1: Resumen Ejecutivo
# Ejecutar desde la raíz: streamlit run app/app.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from theme import setup_theme, make_plotly_layout

# ── Configuración global ──────────────────────────────────────
st.set_page_config(
    page_title="Percepción de la IA — TFG",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Tema ──────────────────────────────────────────────────────
T = setup_theme()

# ── Rutas ─────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
YT_PATH  = DATA_DIR / "youtube_sentiment_v2.parquet"
TW_PATH  = DATA_DIR / "tweets_op_sectored.parquet"

# ── Constantes compartidas (importadas por pages/) ────────────
COLORS = {
    "negative": T["negative"],
    "neutral":  T["neutral"],
    "positive": T["positive"],
    "accent":   T["accent"],
    "twitter":  T["twitter"],
    "youtube":  T["youtube"],
    "surface":  T["surface"],
    "border":   T["border"],
    "text":     T["text"],
    "muted":    T["muted"],
}

LABEL_ES = {
    "negative": "Negativo",
    "neutral":  "Neutral",
    "positive": "Positivo",
}

PLOTLY_LAYOUT = make_plotly_layout(T)

# ── Carga de datos ────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos YouTube…")
def load_yt():
    df = pd.read_parquet(YT_PATH)
    df["date"]          = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df["comment_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year"]          = df["date"].dt.year
    df["fase"] = df["year"].apply(
        lambda y: "Pre-ChatGPT" if y <= 2022 else "Era ChatGPT"
    )
    return df

@st.cache_data(show_spinner="Cargando datos Twitter…")
def load_tw():
    df = pd.read_parquet(TW_PATH)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["year"]       = df["created_at"].dt.year
    return df

# ════════════════════════════════════════════════════════════
#  RESUMEN EJECUTIVO
# ════════════════════════════════════════════════════════════

st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;'
    f'letter-spacing:0.15em;color:{T["accent"]};text-transform:uppercase;'
    f'margin-bottom:6px">Resumen ejecutivo</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<h1 style="font-size:clamp(24px,3vw,34px);font-weight:900;'
    f'color:{T["text"]};margin-bottom:8px;line-height:1.15">'
    f'¿Cómo ha evolucionado la percepción pública de la Inteligencia Artificial?</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="color:{T["muted"]};font-size:16px;margin-bottom:24px;line-height:1.6">'
    f'Análisis de sentimiento sobre 186.378 textos de Twitter (2017–2021) y '
    f'YouTube (2020–2026) mediante modelos transformer.</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Carga ─────────────────────────────────────────────────────
try:
    yt = load_yt()
    tw = load_tw()
except FileNotFoundError as e:
    st.error(f"Parquet no encontrado en `data/processed/`.\n\n`{e}`")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────
neg_global    = (yt["sentiment_label"] == "negative").mean() * 100
neg_pre = (
    yt[yt["year"].isin([2020, 2021, 2022])]["sentiment_label"] == "negative"
).mean() * 100
neg_post      = (yt[yt["fase"] == "Era ChatGPT"]["sentiment_label"] == "negative").mean() * 100
delta_chatgpt = neg_post - neg_pre
neg_tw        = (tw["sentiment_label_hf"] == "negative").mean() * 100
total_textos  = len(yt) + len(tw)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("NEGATIVIDAD YOUTUBE",
              f"{neg_global:.1f}%",
              f"vs {neg_pre:.1f}% antes de ChatGPT",
              delta_color="inverse")
with c2:
    st.metric("NEGATIVIDAD TWITTER",
              f"{neg_tw:.1f}%",
              f"{len(tw):,} tweets de opinión (sin URL)",
              delta_color="off")
with c3:
    st.metric("PUNTO DE INFLEXIÓN",
              f"+{delta_chatgpt:.0f}pp",
              "Negatividad pre → post ChatGPT (nov 2022)",
              delta_color="inverse")
with c4:
    st.metric("TOTAL TEXTOS ANALIZADOS",
              f"{total_textos/1000:.0f}k",
              f"{yt['video_id'].nunique()} vídeos · "
              f"{yt['channel'].nunique()} canales · 2017–2026",
              delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tarjetas hipótesis ────────────────────────────────────────
CARD = (
    f'<div style="background:{T["surface"]};border:1px solid {T["border"]};'
    f'border-radius:8px;padding:20px;height:100%">'
    f'<h3 style="font-size:22px;font-family:\'Playfair Display\',serif;'
    f'color:{T["text"]};margin-bottom:10px">{{title}}</h3>'
    f'<p style="font-size:15px;color:{T["text2"]};line-height:1.65">{{body}}</p>'
    f'</div>'
)

h1, h2, h3 = st.columns(3)
with h1:
    st.markdown(CARD.format(
        title="Polarización creciente",
        body="La negatividad en YouTube sube del 35.3% (2021) al 60.7% (2026). "
             "ChatGPT (nov 2022) actúa como punto de inflexión: +7.6pp en un solo año."
    ), unsafe_allow_html=True)
with h2:
    st.markdown(CARD.format(
        title="Diferenciación por sectores",
        body="Empleo concentra la mayor negatividad (60.9%) y educación la menor (47.7%). "
             "La brecha se amplía tras ChatGPT: educación +20pp, empleo +15pp."
    ), unsafe_allow_html=True)
with h3:
    st.markdown(CARD.format(
        title="Diferenciación por plataforma",
        body="Twitter más neutral (56.7%) y positivo, YouTube más negativo (52.9%) "
             "y extenso. La diferencia es real pero parcialmente metodológica."
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Gráficos ──────────────────────────────────────────────────
col_l, col_r = st.columns(2)

# Doughnut
with col_l:
    st.markdown(
        f'<p style="font-family:\'Playfair Display\',serif;font-size:19px;'
        f'font-weight:700;color:{T["text"]};margin-bottom:4px">Distribución global — YouTube</p>'
        f'<p style="font-family:\'DM Mono\',monospace;font-size:13px;'
        f'color:{T["muted"]};margin-bottom:12px">'
        f'{len(yt):,} comentarios · 2020–2026</p>',
        unsafe_allow_html=True,
    )
    dist = yt["sentiment_label"].value_counts()
    labels_es = [LABEL_ES.get(l, l) for l in dist.index]
    fig_donut = go.Figure(go.Pie(
        labels=labels_es,
        values=dist.values,
        hole=0.62,
        marker_colors=[COLORS.get(l, T["muted"]) for l in dist.index],
        textfont=dict(family="DM Mono, monospace", size=14, color="#ffffff"),
        hovertemplate="%{label}: %{value:,} comentarios (%{percent})<extra></extra>",
        hoverinfo="label+percent",
    ))
    fig_donut.update_layout(**{
        **PLOTLY_LAYOUT,
        "height":     320,
        "showlegend": True,
        "legend": dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=16, color=T["text"], family="DM Sans, sans-serif"),
            itemsizing="constant",
            traceorder="normal",
        ),
        "margin": dict(l=0, r=0, t=10, b=60),
    })
    st.plotly_chart(fig_donut, use_container_width=True)

# Bar negatividad anual
with col_r:
    st.markdown(
        f'<p style="font-family:\'Playfair Display\',serif;font-size:19px;'
        f'font-weight:700;color:{T["text"]};margin-bottom:4px">Negatividad por año — YouTube</p>'
        f'<p style="font-family:\'DM Mono\',monospace;font-size:13px;'
        f'color:{T["muted"]};margin-bottom:12px">% negativo · H1</p>',
        unsafe_allow_html=True,
    )
    neg_anual = (
        yt.groupby("year")["sentiment_label"]
        .apply(lambda s: (s == "negative").mean() * 100)
        .reset_index()
        .rename(columns={"sentiment_label": "pct_neg"})
    )
    fig_bar = go.Figure(go.Bar(
        x=neg_anual["year"].astype(str),
        y=neg_anual["pct_neg"].round(1),
        marker_color=[
            T["negative"] if v > 50 else T["negative_faded"]
            for v in neg_anual["pct_neg"]
        ],
        text=neg_anual["pct_neg"].round(1).astype(str) + "%",
        textposition="outside",
        textfont=dict(family="DM Mono, monospace", size=13, color=T["text"]),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig_bar.update_layout(**{
        **PLOTLY_LAYOUT,
        "height": 320,
        "yaxis":  dict(range=[25, 70], ticksuffix="%",
                       gridcolor=T["border"], tickfont=dict(size=13, color=T["muted"])),
        "xaxis":  dict(gridcolor="rgba(0,0,0,0)",
                       tickfont=dict(size=13, color=T["muted"])),
        "margin": dict(l=0, r=10, t=10, b=10),
    })
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<p style="font-family:\'DM Mono\',monospace;font-size:12px;color:{T["muted"]}">'
    f'Modelo: cardiffnlp/twitter-xlm-roberta-base-sentiment · '
    f'YouTube: youtube_sentiment_v2.parquet · '
    f'Twitter: tweets_op_sectored.parquet · '
    f'Guadalupe Martínez Blanco · GITT + BA · 2025</p>',
    unsafe_allow_html=True,
)
