from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from data_loader import load_twitter_opinion, load_youtube_sentiment
from theme import (
    COLORS,
    PLOTLY_BASE_LAYOUT,
    get_theme_tokens,
)

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

_SENT_COLORS = [COLORS["negative"], COLORS["neutral"], COLORS["positive"]]
_SENT_LABELS = ["Negativo", "Neutral", "Positivo"]
_SENT_KEYS = ["negative", "neutral", "positive"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sentiment_donut(counts: dict, center: str) -> go.Figure:
    tokens = get_theme_tokens()
    vals = [counts.get(k, 0) for k in _SENT_KEYS]

    fig = go.Figure(go.Pie(
        labels=_SENT_LABELS,
        values=vals,
        hole=0.6,
        marker=dict(colors=_SENT_COLORS, line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(
            size=14,
            family="Geist Mono, monospace",
            color="white",
        ),
        direction="clockwise",
        sort=False,
    ))

    layout = {**PLOTLY_BASE_LAYOUT}
    layout.update(
        height=320,
        margin=dict(l=8, r=8, t=8, b=8),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.04,
            xanchor="center",
            x=0.5,
            font=dict(size=11, family="Geist Mono, monospace", color=tokens["text2"]),
        ),
        annotations=[dict(
            text=center,
            x=0.5, y=0.5,
            font=dict(size=18, family="Instrument Serif, serif", color=tokens["text"]),
            showarrow=False,
        )],
    )
    fig.update_layout(**layout)
    return fig


def _kpi(label: str, value: str, detail: str, cls: str) -> str:
    return (
        f'<div class="kpi-card {cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value kpi-val-{cls.split()[0][4:]}">{value}</div>'
        f'<div class="kpi-detail">{detail}</div>'
        f'</div>'
    )


# ── Page ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Data ─────────────────────────────────────────────────────────────────
    tw = load_twitter_opinion()
    yt = load_youtube_sentiment()

    tw_sent = tw["sentiment_label_hf"].value_counts().to_dict()
    yt_sent = yt["sentiment_label"].value_counts().to_dict()
    tw_total = len(tw)
    yt_total = len(yt)

    tw_year_min = int(tw["date"].dt.year.min())
    tw_year_max = int(tw["date"].dt.year.max())
    yt_year_max = int(yt["comment_year"].max())

    neg_yt_pct = yt_sent.get("negative", 0) / yt_total * 100
    neu_tw_pct = tw_sent.get("neutral", 0) / tw_total * 100

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-wrap">
            <div class="section-tag">01 · Visión general</div>
            <h1 class="section-title">Visión general del análisis</h1>
            <p class="section-subtitle">
                Dos plataformas, nueve años de opinión pública sobre inteligencia artificial.
                186&nbsp;378 textos analizados con el mismo modelo de NLP para garantizar comparabilidad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            _kpi("Twitter", f"{tw_total:,}",
                 f"tweets sin URL · {tw_year_min}–{tw_year_max}", "kpi-tw"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _kpi("YouTube", f"{yt_total:,}",
                 f"comentarios · 2020–{yt_year_max}", "kpi-yt"),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _kpi("Modelo NLP", "XLM-RoBERTa",
                 "cardiffnlp · sentiment", "kpi-accent"),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            _kpi("Período total", f"{tw_year_min}–{yt_year_max}",
                 f"{tw_year_min}–{tw_year_max} Twitter · 2020–{yt_year_max} YouTube",
                 "kpi-accent"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Donut charts ─────────────────────────────────────────────────────────
    col_tw, col_yt = st.columns(2)

    with col_tw:
        with st.container(border=True):
            st.markdown(
                f'<p class="chart-title">Sentimiento global — Twitter</p>'
                f'<p class="chart-desc">Solo tweets sin URL · señal de opinión directa'
                f' (n={tw_total:,})</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _sentiment_donut(tw_sent, "Twitter"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    with col_yt:
        with st.container(border=True):
            st.markdown(
                f'<p class="chart-title">Sentimiento global — YouTube</p>'
                f'<p class="chart-desc">Comentarios con ≥10 palabras'
                f' (n={yt_total:,})</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                _sentiment_donut(yt_sent, "YouTube"),
                use_container_width=True,
                config={"displayModeBar": False},
                theme=None,
            )

    # ── Insight ───────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Hallazgo central:</strong> Twitter (pre-ChatGPT) muestra un sentimiento
            dominado por la neutralidad ({neu_tw_pct:.1f}%), mientras YouTube (que cubre la
            era post-ChatGPT) invierte la proporción con un {neg_yt_pct:.1f}% de negatividad.
            El contraste revela un cambio de paradigma en la percepción pública.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

    # ── Hypothesis cards ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-tag" style="margin-bottom:14px">Hipótesis de trabajo</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hyp-grid">
            <div class="hyp-card">
                <h4>Evolución hacia la negatividad</h4>
                <p>La percepción pasa de neutral-curiosa a dominantemente negativa. ChatGPT
                (nov 2022) actúa como catalizador visible, no como causa única.</p>
            </div>
            <div class="hyp-card">
                <h4>Diferenciación por sectores</h4>
                <p>Empleo concentra 60.9% de negatividad. Educación es genuinamente
                ambivalente: la tutoría IA genera esperanza, pero el sistema institucional
                genera miedo.</p>
            </div>
            <div class="hyp-card">
                <h4>Diferenciación por plataforma</h4>
                <p>Las plataformas difieren, pero no como se esperaba. YouTube no es más
                equilibrado: la mayor extensión amplifica la negatividad, no la mitiga.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Method note ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="method-note">
            <strong>Decisión metodológica clave:</strong> El 86% de los tweets contienen
            URLs y son actos de difusión (sharing), no de opinión. Su sentimiento es ~75%
            neutral. Se filtran para aislar la señal real (14% restante → 123&nbsp;389 tweets).
            Modelo: <code>cardiffnlp/twitter-xlm-roberta-base-sentiment</code> aplicado en
            ambas plataformas para garantizar comparabilidad.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
